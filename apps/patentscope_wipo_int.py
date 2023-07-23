import pandas as pd
import xmltodict
from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.patentscope_wipo_int import PatentScopeWipoSpider
from utils.config import *
from utils.constants import ACTION_SCRAPPING, ACTION_CONVERT
from utils.helpers import write_results_to_csv


def start_scrapper(site_name, action_type, target_year=None, target_start_week=None, target_end_week=None,
                   scraping_target=None):
    if action_type == ACTION_SCRAPPING:
        feed_format = 'csv'

        category_file_path = os.path.join(OUTPUT_DIR, f'{site_name}_categories.{feed_format}')
        result_list_suc_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_year}.{feed_format}')
        result_list_err_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{target_year}_err.{feed_format}')

        feed_uri = os.path.join(
            OUTPUT_RESULT_DIR, f'{site_name}_{target_year}_{target_start_week}_{target_end_week}_result.{feed_format}'
        )

        process = CrawlerProcess()

        process.crawl(PatentScopeWipoSpider, param={
            'action_type': action_type,
            'target_year': target_year,
            'target_start_week': target_start_week,
            'target_end_week': target_end_week,
            'scraping_target': scraping_target,
            'category_file_path': category_file_path,
            'result_list_suc_f_path': result_list_suc_f_path,
            'result_list_err_f_path': result_list_err_f_path,
            'feed_uri': feed_uri
        })

        process.start()

    elif action_type == ACTION_CONVERT:
        for f in os.listdir(OUTPUT_TEMP_DIR):
            input_f_path = os.path.join(OUTPUT_TEMP_DIR, f)
            df = pd.read_excel(input_f_path)
            week_num_list = df.iloc[0, 0].replace('Gazette: ', '').split('/')
            week_num_list.reverse()
            week_num = ''.join(week_num_list)
            df = df.drop(df.index[0])
            output_f_path = os.path.join(OUTPUT_LIST_DIR, f'{site_name}_list_{week_num}.csv')
            df.to_csv(output_f_path, index=None, header=False)
    else:
        pass


def parse_xml(site_name):
    input_dir = os.path.join(OUTPUT_RESULT_DIR, site_name, "raw")
    input_f_path = os.path.join(input_dir, "AT2022060350-IASR.xml")
    with open(input_f_path) as f:
        raw_data = xmltodict.parse(f.read())
        print(raw_data)
        bibliographic_data = raw_data["wo-international-application-status"]["wo-bibliographic-data"]
        publication_data = bibliographic_data["publication-reference"]["document-id"]

        publication_number = f'{publication_data["country"]}/{publication_data["doc-number"]}'
        publication_date = publication_data["date"]
        application_number = bibliographic_data["application-reference"]["document-id"]["doc-number"]
        filing_date = bibliographic_data["application-reference"]["document-id"]["date"]
        priority_date = bibliographic_data["wo-priority-info"]["priority-claim"]["date"]
        ipc_raw_items = bibliographic_data["classifications-ipcr"]["classification-ipcr"]
        ipc_items = []
        for item in ipc_raw_items:
            ipc_item = f"{item['section']}{item['class']}{item['subclass']} {item['main-group']}/{item['subgroup']}" \
                       f" ({item['ipc-version-indicator']['date']})"
            ipc_items.append(ipc_item)
        ipc = "; ".join(ipc_items)

        applicant_raw_items = bibliographic_data['parties']['applicants']['applicant']
        applicants = []
        inventor_raw_items = bibliographic_data['parties']['inventors']['inventor']
        inventors = []
        agent_raw_items = bibliographic_data['parties']['agents']['agent']
        agents = []

        titles = bibliographic_data['invention-title']
        title_en = titles[0]['#text']
        abstracts = raw_data["wo-international-application-status"]['abstract']
        abstract_en = abstracts[0]['p']['#text']

        output_item = {
            "publication_number": publication_number,
            "publication_date": publication_date,
            "application_number": application_number,
            "filing_date": filing_date,
            "priority_date": priority_date,
            "international_patent_classification": ipc,
            "applicants": applicants,
            "inventors": inventors,
            "agents": agents,
            "title_en": title_en,
            "abstract_en": abstract_en,
        }
        output_items = [output_item]

        output_dir = os.path.join(OUTPUT_RESULT_DIR, site_name)
        output_f_path = os.path.join(output_dir, 'tmp')
        write_results_to_csv(output_f_path, output_items)
