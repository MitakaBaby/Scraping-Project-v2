from common import Utils
from scheduling import sites_to_run
from scrapemethods import Methods

if __name__ == "__main__":
    while True:
        sites = sites_to_run()
        for site in sites:
            config = Utils.load_configs(site)
            method_name = config.get("scrape_method")
            if method_name:
                site_processor = Methods()
                if hasattr(site_processor, method_name):
                    try:
                        method_to_call = getattr(site_processor, method_name)
                        method_to_call(site)
                    except Exception as e:
                        print(e)
                        continue
