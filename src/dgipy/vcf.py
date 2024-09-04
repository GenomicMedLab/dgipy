"""Provides methods for annotating VCF with DGIdb data"""

import contextlib
from itertools import groupby
from pathlib import Path

import pandas as pd
import pysam
import requests
from tqdm import tqdm

import dgipy


# TODO: Probably need another class as a wrapper object rather than putting it all in a list
# Class would have analogous display methods but also allow access to individual GeneResults
class GeneResult:
    """A gene result from original VCF
    .. code-block:: python
        import vcf

        # Provide path to VCF file and specify chromosome
        data = vcf.annotate("link/to/file", chr="chr#")
    """

    def __init__(self, data: list) -> None:
        """Initialize a gene with a name, VCF records, and drug-gene interactions"""
        # TODO: handle genes without names, 'novel transript'
        try:
            self.gene = data[0]["name"]
        except:
            self.gene = "None"

        self.records = data
        self.interactions = dgipy.get_interactions(self.gene)

        # TODO: handle app searches with blank lists [], currently FDA resource hangs for awhile?
        if not list(self.interactions["drug"].values):
            self.applications = "None"
        else:
            self.applications = dgipy.get_drug_applications(
                list(self.interactions["drug"].values)
            )

        self.gene_info = dgipy.get_genes(self.gene)
        self.categories = dgipy.get_categories(self.gene)


def annotate(filepath: Path, contig: str) -> pd.DataFrame:
    """Map chr,pos pairs from a VCF file to human genes and search DGIdb for drug-gene interactions

    :param filepath: link to a valid VCF file
    :param contig: specified chromosome (i.e. chr7)
    :return: Dataframe of drug-gene interactions
    """
    if not isinstance(filepath, Path):
        msg = "Filepath argument must be a valid pathlib.Path object"
        raise ValueError(msg)

    # Open VCF file
    records = _process_vcf(filepath, contig)
    # Grab records & relevant info (params: chr7)
    mapped = _ensembl_map(records)  # TODO: modularize mapping
    # Group records with like-genes
    grouped = _group_by_name(mapped)
    # Instance each gene set as a class
    return [GeneResult(grouped[gene]) for gene in grouped]


def _process_vcf(filepath: Path, contig: str) -> list:
    """Grab relevant data for mapping and mutations from starting VCF

    :param filepath: link to valid VCF file
    :param contig: specified chromosome (i.e. chr7)
    :return: List of record dicts

    """
    # TODO: Add support for pysam.VariantFile
    # https://pysam.readthedocs.io/en/latest/usage.html#working-with-vcf-bcf-formatted-files

    file = pysam.TabixFile(str(filepath.absolute()))

    records = []
    for record in tqdm(file.fetch(contig)):
        fields = record.split("\t")
        entry = {
            "chromosome": fields[0],
            "pos": fields[1],
            "ref": fields[3],
            "alt": fields[4],
            "qual": fields[5],
            "filter": fields[6],
        }
        records.append(entry)

    return records


def _get_gene_by_position(chromosome: str, position: str) -> list:
    """Map chr,pos pair to genome via ensembl

    :param chromosome: specified chromosome (i.e. chr7)
    :param position: genomic coordinate
    :return: genomic info for specified coordinate
    """
    url = f"https://rest.ensembl.org/overlap/region/human/{chromosome}:{position}-{position}?feature=gene"
    headers = {"Content-Type": "application/json"}
    response = requests.get(f"{url}", headers=headers, timeout=10)

    if not response.ok:
        response.raise_for_status()
        return None

    return response.json()


def _ensembl_map(records: list) -> list:
    """Take VCF input and map to ensembl

    :param records: list of records pulled from VCF
    :return: list of mapped genes
    """
    results = []
    # TODO: Allow custom slice selection as data sets can be huge, currently slicing 0:1500 or 0:150 for time purposes
    for record in tqdm(records[0:1500]):
        gene_info = _get_gene_by_position(record["chromosome"], record["pos"])

        if type(gene_info) is None:
            continue

        for info in gene_info:
            entry = {}
            if info["feature_type"] == "gene":
                with contextlib.suppress(KeyError):  # TODO: handle genes without names
                    entry["name"] = info["external_name"]

                entry["desc"] = info["description"]
                entry["gene_id"] = info["gene_id"]
                entry.update(record)
                results.append(entry)

    return results


def _group_by_name(data: list, default_name: str = "Unknown") -> dict:
    """Take list of records and group to dict by gene name

    :param data: list of records
    :param default_name: name of gene if none found
    :return: dict of records grouped by gene name
    """
    sorted_data = sorted(data, key=lambda x: x.get("name", default_name))

    return {
        key: list(group)
        for key, group in groupby(
            sorted_data, key=lambda x: x.get("name", default_name)
        )
    }
