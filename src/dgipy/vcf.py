"""Provides methods for annotating VCF with DGIdb data"""

import contextlib
from itertools import groupby

import pandas as pd
import pysam
import requests
from tqdm import tqdm

import dgipy

# Sample usage: import vcf
#               data = vcf.annotate('link/to/file',chr='chr#')


# TODO: Probably need another class as a wrapper object rather than putting it all in a list
# Class would have analogous display methods but also allow access to individual GeneResults
class GeneResult:
    """A gene result from original VCF

    Attributes
    ----------
    gene : str
        The name of the gene
    records : list
        The mapped records from original VCF
    interactions : pd.DataFrame
        The interactions obtained from DGIdb

    Methods
    -------
    search_interactions(gene: str) -> pd.DataFrame
        Search drug-gene interactions for given gene in DGIdb

    """

    def __init__(self, data: list) -> None:
        """Initialize a gene with a name, VCF records, and drug-gene interactions"""
        # TODO: handle genes without names, 'novel transript'
        try:
            self.gene = data[0]["name"]
        except:
            self.gene = "None"

        self.records = data
        self.interactions = self.search_interactions(self.gene)

        # TODO: handle app searches with blank lists [], currently FDA resource hangs for awhile?
        if not list(self.interactions["drug"].values):
            self.applications = "None"
        else:
            self.applications = self.search_applications(
                list(self.interactions["drug"].values)
            )

        self.gene_info = self.grab_gene_info(self.gene)
        self.categories = self.grab_categories(self.gene)

    # TODO: These can probably just be simpilifed to direct assignment during __init__ but might be useful this way too
    def search_interactions(self, gene: str) -> pd.DataFrame:
        """Search drug-gene interactions for given gene in DGIdb

        :param gene: the name of the gene
        :return: Dataframe of drug-gene interactions
        """
        return dgipy.get_interactions(gene)

    def search_applications(self, drugs: list) -> pd.DataFrame:
        """Search for drug applications for interaction drugs in DGIdb

        :param drugs: list of drugs from interaction results
        :return: Dataframe of FDA applications
        """
        return dgipy.get_drug_applications(drugs)

    def grab_gene_info(self, gene: str) -> pd.DataFrame:
        """Grab gene information from DGIdb

        :param gene: gene name
        :return: Dataframe of gene information
        """
        return dgipy.get_gene(gene)

    def grab_categories(self, gene: str) -> pd.DataFrame:
        """Grab gene categories from DGIdb

        :param gene: gene name
        :return: Dataframe of gene categories
        """
        return dgipy.get_categories(gene)


def annotate(filepath: str, contig: str) -> pd.DataFrame:
    """Map chr,pos pairs from a VCF file to human genes and search DGIdb for drug-gene interactions

    :param filepath: link to a valid VCF file
    :param contig: specified chromosome (i.e. chr7)
    :return: Dataframe of drug-gene interactions
    """
    # Open VCF file
    records = _process_vcf(filepath, contig)
    # Grab records & relevant info (params: chr7)
    mapped = _ensembl_map(records)  # TODO: modularize mapping
    # Group records with like-genes
    grouped = _group_by_name(mapped)
    # Instance each gene set as a class
    vcf_results = []
    for gene in grouped:
        vcf_results.append(GeneResult(grouped[gene]))

    return vcf_results


def _process_vcf(filepath: str, contig: str) -> list:
    """Grab relevant data for mapping and mutations from starting VCF

    :param filepath: link to valid VCF file
    :param contig: specified chromosome (i.e. chr7)
    :return: List of record dicts

    """
    file = pysam.TabixFile(filepath)

    records = []
    for record in tqdm(file.fetch(contig)):
        fields = record.split("\t")
        entry = {}
        entry["chromosome"] = fields[0]
        entry["pos"] = fields[1]
        entry["ref"] = fields[3]
        entry["alt"] = fields[4]
        entry["qual"] = fields[5]
        entry["filter"] = fields[6]
        records.append(entry)

    return records


def _get_gene_by_position(chromosome: str, position: str) -> list:
    """Map chr,pos pair to genome via ensembl

    :param chromosome: specified chromosome (i.e. chr7)
    :param position: genomic coordinate
    :return: genomic info for specified coordinate
    """
    server = "https://rest.ensembl.org"
    ext = f"/overlap/region/human/{chromosome}:{position}-{position}?feature=gene"

    headers = {"Content-Type": "application/json"}
    response = requests.get(f"{server}{ext}", headers=headers, timeout=10)

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
