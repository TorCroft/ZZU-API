from requests import post, get
from .logger import logger
from .config import config

class CustomExpection(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

class ZZU_Login_Error(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)


class ZZU_API:
    def __init__(self) -> None:
        self.username = config.Account
        self.password = config.Password

        self.host = "https://token.s.zzu.edu.cn"
        self.ecard_host = "https://ecard.v.zzu.edu.cn"

    def login(self):
        path = "/password/passwordLogin"
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
            "X-Device-Infos": "packagename=com.lantu.MobileCampus.zzu;version=2.3.2;system=iOS",
            "Accept": "application/json",
            "User-Agent": "SWSuperApp/2.3.2 (iPhone; iOS 17.0.2; Scale/3.00)",
            "Accept-Language": "zh-CN",
            "Accept-Encoding": "gzip, deflate, br",
        }
        body = {
            "appId": "com.lantu.MobileCampus.zzu",
            "clientId": "477e40a75443827bf1e1fc9eee94f561",
            "deviceId": "79C26735-C663-4708-9C69-8108E2E9ECD8",
            "mfaState": "",
            "osType": "iOS",
            "password": self.password,
            "username": self.username,
        }
        response: dict = post(url=self.host + path, headers=header, data=body).json()
        if int(response.get("code")) != 0:
            raise ZZU_Login_Error(response.get("message"))
        config.UserToken = response["data"]["idToken"]
        config.save_config()

    def get_jid_and_tid(self):
        path = "/server/auth/host/open"
        query_params = {"host": "11", "org": "2", "X-Id-Token": "..."}
        headers = {
            "Sec-Fetch-Site": "none",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Mode": "navigate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
            "X-Id-Token": config.UserToken,
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = get(self.ecard_host + path, params=query_params, headers=headers)
        config.JsessionId = response.history[0].cookies.get("JSESSIONID")
        config.Tid = response.history[0].headers.get("Location").split("?tid=")[1]
        logger.debug(f"\nJsessionid {config.JsessionId}\nTid{config.Tid}")
        config.save_config()

    def get_ecard_token(self):
        path = "/server/auth/getToken"
        headers = {
            "Accept": "*/*",
            "Authorization": "",
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "Content-Type": "application/json",
            "Origin": "https://ecard.v.zzu.edu.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Cookie": f"JSESSIONID={config.JsessionId}; userToken={config.UserToken}",
        }
        body = {"tid": config.Tid}
        response: dict = post(url=self.ecard_host + path, headers=headers, json=body).json()
        if not response.get("success"):
            raise ZZU_Login_Error(response.get("message"))
        config.RefreshToken = response["resultData"]["refreshToken"]
        config.ECardAccessToken = response["resultData"]["accessToken"]
        logger.debug(f"\nACCESS_TOKEN {config.ECardAccessToken}\nREFRESH_TOKEN {config.RefreshToken}")
        config.save_config()
    
    def refresh_access_token(self):
        path = "/server/auth/updateToken"
        headers = {
            "Accept": "*/*",
            "Authorization": config.ECardAccessToken,
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "Content-Type": "application/json",
            "Origin": "https://ecard.v.zzu.edu.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Cookie": f"JSESSIONID={config.JsessionId}; userToken={config.UserToken}",
        }
        body = {
            "refreshToken": config.RefreshToken
        }
        response: dict = post(url=self.ecard_host + path, headers=headers, json=body).json()
        if not response.get("success"):
            raise CustomExpection(response.get("message"))
        config.RefreshToken = response["resultData"]["refreshToken"]
        config.ECardAccessToken = response["resultData"]["accessToken"]
        logger.debug(f"\nACCESS_TOKEN {config.ECardAccessToken}\nREFRESH_TOKEN {config.RefreshToken}")
        config.save_config()
    
    def get_balance(self):
        path= "/server/recharge/config"
        headers = {
            "Accept": "*/*",
            "Authorization": config.ECardAccessToken,
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "Content-Type": "application/json",
            "Origin": "https://ecard.v.zzu.edu.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Cookie": f"JSESSIONID={config.JsessionId}; userToken={config.UserToken}",
        }
        response: dict = post(url=self.ecard_host + path, headers=headers).json()
        if not response.get("success"):
            raise CustomExpection(response.get("message"))
        data = response["resultData"]
        logger.info(f'{data["idSerial"]} {data["username"]} Balance: {data["balance"]} CNY.')
        return data["balance"]

    def c2c_transaction(self, from_id: str, to_id: str, amount: int, card_password: str):
        path = "/server/c2cTransaction/transferFromCard2Card"
        headers = {
            "Accept": "*/*",
            "Authorization": config.ECardAccessToken,
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "Content-Type": "application/json",
            "Origin": "https://ecard.v.zzu.edu.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Cookie": f"JSESSIONID={config.JsessionId}; userToken={config.UserToken}",
        }
        body = {
            "fromIdSerial": from_id,
            "toIdSerial": to_id,
            "txAmt": amount,
            "password": card_password,
        }
        response: dict = post(url=self.ecard_host + path, headers=headers, json=body).json()
        if not response.get("success"):
            raise CustomExpection(response.get("message"))
        logger.info(f"Transfered {amount} CNY from {from_id} to {to_id}.")
