from requests import post
from .utils import get_today_date_str, timestamp_13_digit, decode_to_json
from .config import config
from .api import ZZU_API

class ZZU_TokenError(Exception):
    def __init__(self, message="You have to provide token to request data."):
        self.message = message
        super().__init__(self.message)


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
