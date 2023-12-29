from requests import post, get
from .utils import get_today_date_str, timestamp_13_digit, decode_to_json
from .logger import logger
from .config import config

REQUIRED_PARAMS = ["building", "area", "level", "room"]

class ResponseError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

class ZZU_Login_Error(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

class ZZU_TokenError(Exception):
    def __init__(self, message="You have to provide token to request data."):
        self.message = message
        super().__init__(self.message)

class ZZU_API:
    def __init__(self) -> None:
        self.username = config.Account
        self.password = config.Password

        self.host = "https://token.s.zzu.edu.cn"
        self.ecard_host = "https://ecard.v.zzu.edu.cn"


    @property
    def __headers_for_ecard(self):
        return {
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
        query_params = {"host": "11", "org": "2", "X-Id-Token": f"{config.UserToken}"}
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
        config.save_config()

    def get_ecard_token(self):
        path = "/server/auth/getToken"
        body = {"tid": config.Tid}
        response: dict = post(url=self.ecard_host + path, headers=self.__headers_for_ecard, json=body).json()
        if not response.get("success"):
            raise ZZU_Login_Error(response.get("message"))
        config.RefreshToken = response["resultData"]["refreshToken"]
        config.ECardAccessToken = response["resultData"]["accessToken"]
        config.save_config()

    def refresh_access_token(self):
        path = "/server/auth/updateToken"
        body = {
            "refreshToken": config.RefreshToken
        }
        response: dict = post(url=self.ecard_host + path, headers=self.__headers_for_ecard, json=body).json()
        if not response.get("success"):
            raise ResponseError(response.get("message"))
        config.RefreshToken = response["resultData"]["refreshToken"]
        config.ECardAccessToken = response["resultData"]["accessToken"]
        config.save_config()

    def get_dorm_location_dict(self):
        path = "/server/utilities/config"
        response: dict = post(url=self.ecard_host + path, headers=self.__headers_for_ecard, json={"utilityType": "electric"}).json()
        if not response.get("success"):
            raise ResponseError(response.get("message"))
        data = response["resultData"]["location"]
        result = {}
        for param in REQUIRED_PARAMS:
            result[param] = data[param]
        result["utilityType"] = "electric"
        return result
    
    def get_account_details(self):
        path = "/server/utilities/account"
        response: dict = post(url=self.ecard_host + path, headers=self.__headers_for_ecard, json=self.get_dorm_location_dict()).json()
        if not response.get("success"):
            raise ResponseError(response.get("message"))
        return response["resultData"]

    def get_balance(self):
        """Return the balance of youur E-Card."""
        data = self.get_account_details()
        balance = data["templateList"][0].get("value")
        logger.info(f'{data["utilityAccount"]} {data["utilityUsername"]} Balance: {data["templateList"][0].get("value")} CNY.')
        return balance

    def get_energy_balance(self):
        """Return the balance of youur energy bill."""
        data = self.get_account_details()["templateList"][3]
        value = data["value"]
        balance = value if value else "None "
        logger.info(f"Electric balance: {balance + data['unit']}")
        return balance

    def c2c_transaction(self, from_id: str, to_id: str, amount: int, card_password: str):
        """Card to card transaction.\n
        `from_id`: 付款人学号\n
        `to_id`: 收款人学号\n
        `amount`: 金额\n
        `card_password`: 校园卡密码，一般是身份证后六位
        """
        path = "/server/c2cTransaction/transferFromCard2Card"
        body = {
            "fromIdSerial": from_id,
            "toIdSerial": to_id,
            "txAmt": amount,
            "password": card_password,
        }
        response: dict = post(url=self.ecard_host + path, headers=self.__headers_for_ecard, json=body).json()
        if not response.get("success"):
            raise ResponseError(response.get("message"))
        logger.info(f"Transfered {amount} CNY from {from_id} to {to_id}.")


class ZZU_Class_Room(ZZU_API):
    def __init__(self) -> None:
        super(ZZU_Class_Room, self).__init__()

        self.jw_host = "https://jw.v.zzu.edu.cn"

    @property
    def base_header(self) -> dict[str, str]:
        return {
            "Host": "jw.v.zzu.edu.cn",
            "Accept": "application/json, text/plain, */*",
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "token": config.Token,
            "Origin": "https://jw.v.zzu.edu.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 SuperApp SuperApp-10459",
            "Referer": "https://jw.v.zzu.edu.cn/app-web/",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Sec-Fetch-Dest": "empty",
            "Cookie": "SVRNAME=ws1",
        }

    def get_jw_token(self):
        '''获取教务系统的token，用于访问教务系统相关资源'''
        path = "/app-ws/ws/app-service/super/app/login-token"
        header: dict = self.base_header
        header["Cookie"] = "SVRNAME=web1"
        header["token"] = None
        data = {
            "userToken": config.UserToken,
            "timestamp": timestamp_13_digit(),
        }
        response: dict = post(url=self.jw_host + path, headers=header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))
        decoded_data = decode_to_json(response["business_data"])
        config.Token = decoded_data["token"]
        config.save_config()

    # fmt: off
    def get_room_data_by_building_id(self, building_id: int | str, date_str: str = get_today_date_str(), retry=True) -> list[dict]:
        """
        `building_id`: required, id of the building you wanna search, such as `5` for `北1`\n
        `date_str`: optional, date string in `%Y-%m-%d` format. Default value is today's date string.
        """
        path = "/app-ws/ws/app-service/room/borrow/occupancy/search"
        data = {
            "building_id": building_id,
            "start_date": date_str,
            "end_date": None,
            "token": config.Token,
            "timestamp": timestamp_13_digit(),
        }
        try:
            response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
            if int(response.get("err_code")) != 0:
                raise ZZU_TokenError(response.get("err_msg"))
        except ZZU_TokenError:
            if retry:
                return self.get_room_data_by_building_id(building_id, date_str, retry=False)
            self.get_jw_token()

        return decode_to_json(response["business_data"])

    def get_campus_building(self) -> list[dict]:
        """Return the names of buildings from all four campus."""
        path = "/app-ws/ws/app-service/room/borrow/campus/building/search"
        data = {
            "authorized": "true",  # Original request is 'False'
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])
    # fmt: on

    def get_semester(self):
        """Return semesters details from 1997, contains start date, end date, season, id, etc."""
        path = "/app-ws/ws/app-service/common/get-semester"
        data = {
            "biz_type_id": "1",  # '1' 代表本科生
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])

    def get_course_table(self, semester_id: int | str, start_date: str, end_date: str):
        """`start_date`: date in `%Y-%m-%d` format.\n
        `end_date`: date in `%Y-%m-%d` format."""

        path = "/app-ws/ws/app-service/student/course/schedule/get-course-tables"
        data = {
            "biz_type_id": "1",
            "semester_id": semester_id,
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])

    def get_time_table(self, semester_id: int):
        path = "/app-ws/ws/app-service/time/setting/course-unit"
        data = {
            "biz_type_id": "1",
            "campus_id": "2",
            "semester_id": semester_id,
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])

    def get_grades(self):
        path = "/app-ws/ws/app-service/student/exam/grade/get-grades"
        data = {
            "biz_type_id": "1",
            "kind": "all",
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])

    def get_exam_tasks(self, semester_id: int):
        path = "/app-ws/ws/app-service/student/exam/schedule/lesson/get-exam-tasks"
        data = {
            "biz_type_id": "1",
            "semester_id": semester_id,
            "timestamp": timestamp_13_digit(),
            "token": config.Token,
        }
        response: dict = post(url=self.jw_host + path, headers=self.base_header, data=data).json()
        if int(response.get("err_code")) != 0:
            raise ZZU_TokenError(response.get("err_msg"))

        return decode_to_json(response["business_data"])