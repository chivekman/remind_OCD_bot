from collections import OrderedDict
import json
import os
import re


# save check up in file with name of user id
def save(check: str, user_id: int) -> None:
    file_name = f'{user_id}.json'
    # if file exists open in r+ mode to read and rewrite file with added check up
    # else open in w mode to create file and write added check up
    if os.path.exists(file_name):
        with open(file_name, 'r+', encoding='utf-8') as f:
            check_ups = OrderedDict(json.load(f))
            check_ups[check] = False
            f.seek(0)
            f.truncate()
            json.dump(check_ups, f)
    else:
        with open(file_name, 'w', encoding='utf-8') as f:
            check_ups = OrderedDict()
            check_ups[check] = False
            f.seek(0)
            f.truncate()
            json.dump(check_ups, f)


# read check ups from the file and return string fromated as list: 1) check-up 2) check ...
def read(user_id: int) -> str:
    with open(f'{user_id}.json', 'r', encoding='utf-8') as f:
        check_ups = json.load(f)
        data = [key for key in check_ups]
        data_str = ''
        count = 1
        for check in data:
            data_str += f"{count}) "
            data_str += check
            data_str += "\n"
            count += 1
        return data_str


# read check ups as list
def read_list(user_id: int) -> list:
    with open(f'{user_id}.json', 'r', encoding='utf-8') as f:
        check_ups = json.load(f)
        data = [key for key in check_ups]
        return data


# get first undone check
def get_check(user_id: int) -> str:
    """
    :param user_id:
    :return: str or "%CHECKED%" if list is empty or all values are True
    """
    with open(f'{user_id}.json', 'r', encoding='utf-8') as f:
        check_ups = json.load(f)
        for check_up, state in check_ups.items():
            if not state:
                return check_up
        return "%CHECKED%"


# rewrite first false check to true
def check_done(user_id: int) -> None:
    with open(f'{user_id}.json', 'r+', encoding='utf-8') as f:
        check_ups = OrderedDict(json.load(f))
        for check, state in check_ups.items():
            if not state:
                check_ups[check] = True
                break
        f.seek(0)
        f.truncate()
        json.dump(check_ups, f)


# move first false check-up to the end of file
def check_not_done(user_id: int) -> None:
    with open(f'{user_id}.json', 'r+', encoding='utf-8') as f:
        check_ups = OrderedDict(json.load(f))
        for check, state in check_ups.items():
            if not state:
                check_ups.move_to_end(check)
                break
        f.seek(0)
        f.truncate()
        json.dump(check_ups, f)


# rewrite all checks to false
def checkups_to_false(user_id: int) -> None:
    with open(f'{user_id}.json', 'r+', encoding='utf-8') as f:
        check_ups = json.load(f)
        for check, state in check_ups.items():
            check_ups[check] = False
        f.seek(0)
        f.truncate()
        json.dump(check_ups, f)


# delete chosen check-ups
def delete(user_id: int, nums: str) -> None:
    pattern = r"[,. ]"
    indexes = [int(i) - 1 for i in re.split(pattern, nums.strip())]  # get list of indexes from numbers given

    with open(f'{user_id}.json', 'r+', encoding='utf-8') as f:
        check_ups_dict = OrderedDict(json.load(f))
        check_ups_list = [key for key in check_ups_dict]

        for check_up in check_ups_list:
            index = check_ups_list.index(check_up)
            if index in indexes:
                check_ups_list[index] = None  # set check-up value to None if it index occurs in index list

        filtered_check_ups = filter(lambda check_up: check_up is not None,
                                    check_ups_list)  # new list without None check-ups
        new_check_ups = {key: False for key in list(filtered_check_ups)}  # new dict friom filtered list

        f.seek(0)
        f.truncate()
        json.dump(new_check_ups, f)


if __name__ == "__main__":
    print("Testing file.py")
    # get_check(556637364)
    # check_done(556637364)
    # checkups_to_false(556637364)
    # save("check", 556637364)
    # check_not_done(556637364)
    # delete(556637364,"1 2 3 4 ")
