import pandas as pd
import xmltodict
from scrapy.crawler import CrawlerProcess

from generic_scraper.spiders.patentscope_wipo_int import PatentScopeWipoSpider
from utils.config import *
from utils.constants import ACTION_SCRAPPING, ACTION_CONVERT
from utils.helpers import write_results_to_csv, convert_date_string_format


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
        output_dir = os.path.join(OUTPUT_RESULT_DIR, site_name, "processed")
        os.makedirs(output_dir, exist_ok=True)

        xml_root_dir = os.path.join(OUTPUT_RESULT_DIR, site_name, "raw")
        week_dirs = [
            os.path.join(xml_root_dir, d)
            for d in os.listdir(xml_root_dir)
            if os.path.isdir(os.path.join(xml_root_dir, d))
        ]
        for week_dir in week_dirs:
            week = os.path.basename(week_dir)
            f_paths = [
                os.path.join(week_dir, f)
                for f in os.listdir(week_dir)
                if os.path.isfile(os.path.join(week_dir, f))
            ]
            for f_path in f_paths:
                parse_xml(f_path, site_name, week, output_dir)
    else:
        pass


def parse_xml(f_path, site_name, week, output_dir):
    with open(f_path) as f:
        raw_data = xmltodict.parse(f.read())
        print(raw_data)
        bibliographic_data = raw_data["wo-international-application-status"]["wo-bibliographic-data"]
        publication_data = bibliographic_data["publication-reference"]["document-id"]

        publication_number = f'{publication_data["country"]}/{publication_data["doc-number"]}'
        _publication_date = publication_data["date"]
        publication_date = convert_date_string_format(_publication_date)
        application_number = bibliographic_data["application-reference"]["document-id"]["doc-number"]
        _filing_date = bibliographic_data["application-reference"]["document-id"]["date"]
        filing_date = convert_date_string_format(_filing_date)
        _priority_date = bibliographic_data.get("wo-priority-info", {}).get("priority-claim", {}).get("date")
        priority_date = convert_date_string_format(_priority_date) if _priority_date else "unknown"

        _ipc_raw_items = bibliographic_data["classifications-ipcr"]["classification-ipcr"]
        ipc_raw_items = _ipc_raw_items if isinstance(_ipc_raw_items, list) else [_ipc_raw_items]
        ipc_items = []
        for item in ipc_raw_items:
            _ipc_date = item['ipc-version-indicator']['date']
            ipc_date = convert_date_string_format(_ipc_date, "%Y%m%d", "%Y.%m")
            ipc_item = f"{item['section']}{item['class']}{item['subclass']} {item['main-group']}/{item['subgroup']}" \
                       f" ({ipc_date})"
            ipc_items.append(ipc_item)
        ipc = "; ".join(ipc_items)

        _applicant_raw_items = bibliographic_data['parties']['applicants']['applicant']
        applicant_raw_items = _applicant_raw_items if isinstance(_applicant_raw_items, list) else [_applicant_raw_items]
        applicants = parse_items(applicant_raw_items)

        _inventor_raw_items = bibliographic_data['parties']['inventors']['inventor']
        inventor_raw_items = _inventor_raw_items if isinstance(_inventor_raw_items, list) else [_inventor_raw_items]
        inventors = parse_items(inventor_raw_items)

        _agent_raw_items = bibliographic_data['parties']['agents']['agent']
        agent_raw_items = _agent_raw_items if isinstance(_agent_raw_items, list) else [_agent_raw_items]
        agents = parse_items(agent_raw_items)

        titles = bibliographic_data['invention-title']
        title_en = ""
        for title in titles:
            if title["@lang"].lower() == "en":
                title_en = title["#text"]
                break
        abstracts = raw_data["wo-international-application-status"]['abstract']
        abstract_en = ""
        for abstract in abstracts:
            if abstract["@lang"].lower() == "en":
                abstract_en = abstract["p"]["#text"]
                break

        output_item = {
            "publication_number": publication_number,
            "publication_date": publication_date,
            "application_number": application_number,
            "filing_date": filing_date,
            "priority_date": priority_date,
            "international_patent_classification": ipc,
            "applicant(s)": applicants,
            "inventor(s)": inventors,
            "agent(s)": agents,
            "title_en": title_en,
            "abstract_en": abstract_en,
        }
        output_items = [output_item]

        output_f_name = f"{site_name}_{week}.csv"
        output_f_path = os.path.join(output_dir, output_f_name)
        write_results_to_csv(output_f_path, output_items)


def parse_items(raw_items):
    delimiter = " ||| "
    items = []
    for raw_item in raw_items:
        inventor_name = raw_item["addressbook"]["name"]["#text"]
        inventor_address = f'{raw_item["addressbook"]["address"]["address-1"]}' \
                           f' ({raw_item["addressbook"]["address"]["country"]})'
        item = f"{inventor_name}; {inventor_address}"
        items.append(item)

    items_str = delimiter.join(items)
    return items_str
