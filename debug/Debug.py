import yaml


class Debug:
    def __init__(self):
        with open('resource/serverconfig.yml', 'r') as yml:
            server_config = yaml.safe_load(yml)
            self.debug_mode = server_config["debug"]
    def debug_info(self, info):
        if self.debug_mode:
            print("[debug]" + info)