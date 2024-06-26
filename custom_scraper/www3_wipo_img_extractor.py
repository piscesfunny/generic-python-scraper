import glob
import os.path

from scrapy.selector import Selector
import base64

from utils.config import OUTPUT_LIST_DIR, OUTPUT_RESULT_DIR

if __name__ == '__main__':
    site_name = "www3_wipo"
    list_dir = os.path.join(OUTPUT_LIST_DIR, site_name)
    if not os.path.exists(list_dir):
        os.makedirs(list_dir)

    result_dir = os.path.join(OUTPUT_RESULT_DIR, site_name)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # Get a list of all files in the directory
    file_pattern = os.path.join(list_dir, '*')
    file_list = glob.glob(file_pattern)
    for idx, f_path in enumerate(file_list):
        if os.path.isfile(f_path):
            progress_msg = f"{idx + 1}/{len(file_list)}"
            try:
                input_f_name = os.path.splitext(os.path.basename(f_path))[0]
                with open(f_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    scrapy_selector = Selector(text=content)
                    item_list_selector = scrapy_selector.css("table > tbody > tr")
                    for item_selector in item_list_selector:
                        try:
                            raw_image_data = item_selector.css("td.image > img::attr(src)").get()
                            if not raw_image_data:
                                continue

                            register_no = item_selector.css("td:nth-child(7) > div > span.text::text").get()
                            image_b64_data = raw_image_data.replace("data:image/png;base64,", "")

                            output_f_ext = raw_image_data.split(";")[0].split("/")[1]
                            output_f_name = f"{register_no}.{output_f_ext}"
                            output_dir_path = os.path.join(result_dir, input_f_name)
                            if not os.path.exists(output_dir_path):
                                os.makedirs(output_dir_path)
                            output_f_path = os.path.join(output_dir_path, output_f_name)
                            with open(output_f_path, "wb") as img_f:
                                img_f.write(base64.b64decode(image_b64_data))
                        except Exception as e:
                            print(f"Failed to process {output_f_name}")
                print(f"Processed - {progress_msg}")
            except Exception as e:
                print(f"Failed to process - {progress_msg} due to {e}")
