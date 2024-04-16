"""Provides methods for annotating VCF with DGIdb data"""

import contextlib

import pandas as pd
import pysam
import requests
from tqdm import tqdm

import dgipy

# /Users/mjc014/Documents/docs/papers/DGIpy/vcf_annotation/HG001_GRCh38_1_22_v4.2.1_benchmark.vcf.gz


def annotate(filepath: str, contig: str) -> pd.DataFrame:
    """Map chr,pos pairs from a VCF file to human genes and search DGIdb for drug-gene interactions

    :param filepath: link to a valid VCF file
    :param contig: specified chromosome (i.e. chr7)
    :return: Dataframe of drug-gene interactions
    """
    # Open VCF file
    records = __process_vcf(filepath, contig)
    # Grab records & relevant info (params: chr7)
    mapped = __ensembl_map(records)

    # Map (TODO: modularize)

    return __query_dgidb(mapped)


def __process_vcf(filepath: str, contig: str) -> list:
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


def __get_gene_by_position(chromosome: str, position: str) -> list:
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


def __ensembl_map(records: list) -> list:
    """Take VCF input and map to ensembl

    :param records: list of records pulled from VCF
    :return: list of mapped genes
    """
    results = []
    # TO DO: Allow custom slice selection as data sets can be huge, current 0:1500 for time purposes
    for record in tqdm(records[0:1500]):
        gene_info = __get_gene_by_position(record["chromosome"], record["pos"])

        if type(gene_info) is None:
            continue

        for info in gene_info:
            entry = {}
            if info["feature_type"] == "gene":
                with contextlib.suppress(KeyError):
                    entry["name"] = info["external_name"]

                entry["desc"] = info["description"]
                entry["gene_id"] = info["gene_id"]
                results.append(entry)

    return results


def __query_dgidb(results: list) -> pd.DataFrame:
    """Search interactions from mapped ensembl results

    :param results: list of mapped records
    :return: dataframe of interaction results
    """
    genes = []
    for result in results:
        with contextlib.suppress(
            AttributeError
        ):  # TODO: handle cases where there is no name better
            genes.append(result["name"])

    genes = list(set(genes))

    # TODO: link original loc / mutation / ref / alt to the interaction result (in one DF?)

    # interactions = interactions[interactions['approval'].str.contains('True')]
    return dgipy.get_interactions(genes)
