import json, os

CONFIG_TEMPLATE = {
    "Account": "",
    "Password": "",
    "UserToken": "",
    "Token": "",
    "JsessionId": "",
    "Tid": "",
    "RefreshToken": "",
    "ECardAccessToken": "",
}


class Config:
    def __init__(self) -> None:
        self.path = "config.json"
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(CONFIG_TEMPLATE, f, ensure_ascii=False)
        self.load_config()

    def load_config(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data: dict = json.load(f)
        for k, v in data.items():
            self.__dict__[k] = v

    def save_config(self, **kwargs):
        data = {}
        for key in CONFIG_TEMPLATE:
            data[key] = self.__dict__[key]
        data.update(**kwargs)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)


config = Config()
