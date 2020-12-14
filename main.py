'''
Created by Dylan Gaines


'''

import pymongo
import csv
import json
import uuid
import time
import numpy as np

from pymongo import MongoClient


def setup_the_database():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]
    salary_loc = '/Users/dylan/PycharmProjects/NBAContractValueDatabase/playersalariesandstats2019_2020.json'
    with open(salary_loc) as f:
        salary_data = json.load(f)
    for player in salary_data:
        player['Name'] = player['Name']
        player['Team'] = player['Team']
        player['Salary'] = int(player['Salary'])
        player['Rookie Scale Contract?'] = player['Rookie Scale Contract?']
        player['VORP'] = int(player['VORP'])
        player['Adjusted_VORP'] = int(player['Adjusted_VORP'])
        player['Win Shares'] = int(player['Win Shares'])
        player['Adjusted Win Shares'] = int(player['Adjusted Win Shares'])
        NBASalaries19to20.insert_one(player)
    print(myclient.list_database_names())
    print(mydb.list_collection_names())


def clear_the_collection():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]
    NBASalaries19to20.drop()
    print(myclient.list_database_names())
    print(mydb.list_collection_names())


def rank_players(min_salary, rookies, avd_metrics, adj_metrics):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]

    name_list = []
    vorp_val_list = []
    win_shares_val_list = []

    min_salary = fix_salary(min_salary)

    if adj_metrics == "Adjusted":
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            name_list.append(answer['Name'])
            div_VORP = answer['Adjusted_VORP'] / answer['Salary']
            div_Shares = answer['Adjusted Win Shares'] / answer['Salary']
            vorp_val_list.append(div_VORP)
            win_shares_val_list.append(div_Shares)

    else:
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Team': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            name_list.append(answer['Name'])
            div_VORP = answer['VORP'] / answer['Salary']
            div_Shares = answer['Win Shares'] / answer['Salary']
            vorp_val_list.append(div_VORP)
            win_shares_val_list.append(div_Shares)

    vorp_val_list = np.array(vorp_val_list)
    win_shares_val_list = np.array(win_shares_val_list)

    vorp_val_list = np.interp(vorp_val_list, (vorp_val_list.min(), vorp_val_list.max()), (0, +100))
    win_shares_val_list = np.interp(win_shares_val_list, (win_shares_val_list.min(), win_shares_val_list.max()),
                                    (0, +100))

    tot_dict = {}

    for counter, key in enumerate(name_list):
        vp_rank = vorp_val_list[counter]
        ws_rank = win_shares_val_list[counter]
        if avd_metrics == "VORP":
            ws_rank = 0
            vp_rank = vp_rank * 2
        elif avd_metrics == "Win Shares":
            vp_rank = 0
            ws_rank = ws_rank * 2
        tot_dict[key] = vp_rank + ws_rank

    sorted_dict = sorted(tot_dict.items(), key=lambda x: x[1], reverse=True)

    rank = 1

    for x in sorted_dict:
        print(rank, ": ", x[0], ": ", (x[1] / 2))
        rank = rank + 1


def rank_teams(rank_type, min_salary, rookies, adj_metrics, avd_metrics):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["NBASalaryDatabase"]
    NBASalaries19to20 = mydb["PlayerSalaries2019-2020"]

    num_players_on_team = {"ATL": 0, "BOS": 0, "BRK": 0, "CHO": 0, "CHI": 0, "CLE": 0, "DAL": 0, "DEN": 0, "DET": 0,
                           "GSW": 0, "HOU": 0, "IND": 0, "LAC": 0, "LAL": 0, "MEM": 0, "MIA": 0, "MIL": 0, "MIN": 0,
                           "NOP": 0, "NYK": 0, "OKC": 0, "ORL": 0, "PHI": 0, "PHO": 0, "POR": 0, "SAC": 0, "SAS": 0,
                           "TOR": 0, "UTA": 0, "WAS": 0}
    tot_value_on_team = {"ATL": 0, "BOS": 0, "BRK": 0, "CHO": 0, "CHI": 0, "CLE": 0, "DAL": 0, "DEN": 0, "DET": 0,
                         "GSW": 0, "HOU": 0, "IND": 0, "LAC": 0, "LAL": 0, "MEM": 0, "MIA": 0, "MIL": 0, "MIN": 0,
                         "NOP": 0, "NYK": 0, "OKC": 0, "ORL": 0, "PHI": 0, "PHO": 0, "POR": 0, "SAC": 0, "SAS": 0,
                         "TOR": 0, "UTA": 0, "WAS": 0}
    avg_per_team = {"ATL": 0, "BOS": 0, "BRK": 0, "CHO": 0, "CHI": 0, "CLE": 0, "DAL": 0, "DEN": 0, "DET": 0,
                    "GSW": 0, "HOU": 0, "IND": 0, "LAC": 0, "LAL": 0, "MEM": 0, "MIA": 0, "MIL": 0, "MIN": 0,
                    "NOP": 0, "NYK": 0, "OKC": 0, "ORL": 0, "PHI": 0, "PHO": 0, "POR": 0, "SAC": 0, "SAS": 0,
                    "TOR": 0, "UTA": 0, "WAS": 0}

    min_salary = fix_salary(min_salary)

    if adj_metrics == "Adjusted":
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Name': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Name': 0, 'VORP': 0, 'Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            div_VORP = answer['Adjusted_VORP'] / answer['Salary']
            div_Shares = answer['Adjusted Win Shares'] / answer['Salary']
            if avd_metrics == "VORP":
                div_Shares = 0
            elif avd_metrics == "Win Shares":
                div_VORP = 0
            tot_score = div_VORP + div_Shares
            num_players_on_team[answer["Team"]] = num_players_on_team[answer["Team"]] + 1
            tot_value_on_team[answer["Team"]] = tot_value_on_team[answer["Team"]] + tot_score
    else:
        if rookies == "Yes":
            salary_agg = [
                {'$project': {'_id': 0, 'Name': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]
        else:
            salary_agg = [
                {'$project': {'_id': 0, 'Name': 0, 'Adjusted_VORP': 0, 'Adjusted Win Shares': 0}},
                {'$match': {'Rookie Scale Contract?': "No"}},
                {'$match': {'Salary': {'$gte': min_salary}}}
            ]

        the_result = NBASalaries19to20.aggregate(salary_agg)

        for answer in the_result:
            div_VORP = answer['VORP'] / answer['Salary']
            div_Shares = answer['Win Shares'] / answer['Salary']
            if avd_metrics == "VORP":
                div_Shares = 0
            elif avd_metrics == "Win Shares":
                div_VORP = 0
            tot_score = div_VORP + div_Shares
            num_players_on_team[answer["Team"]] = num_players_on_team[answer["Team"]] + 1
            tot_value_on_team[answer["Team"]] = tot_value_on_team[answer["Team"]] + tot_score

    for team in avg_per_team:
        num_players = num_players_on_team[team]
        tot_value = tot_value_on_team[team]
        avg_per_team[team] = tot_value / num_players

    if rank_type == "Average":
        sorted_dict = sorted(avg_per_team.items(), key=lambda x: x[1], reverse=True)
    else:
        sorted_dict = sorted(tot_value_on_team.items(), key=lambda x: x[1], reverse=True)

    rank = 1

    for x in sorted_dict:
        print(x[0])
        rank = rank + 1
        #rank, ": ", 

def fix_salary(salary):
    if ',' in str(salary):
        salary = salary.replace(',', '')
    salary = int(salary)
    return salary


def Custom_or_Default():
    choice = input("Would you like to use the default criteria or would you like to customize your results? "
                   "(Respond with Default or Customize):\n")
    if choice == "customize" or choice == "custom":
        choice = "Customize"
        return choice
    elif choice == "default":
        choice = "Default"
        return choice
    else:
        print("Please enter a valid response")
        Custom_or_Default()

def Get_Rookies():
    rookies = input("Would you like to include rookie contracts?" " Input Yes or No:\n")
    if rookies == "yes":
        rookies = "Yes"
        return rookies
    elif rookies == "no":
        rookies = "No"
        return rookies
    elif rookies != "Yes" and rookies != "No":
        print("Please enter a valid response")
        Get_Rookies()
    else:
        return rookies


def Get_Advanced():
    avd = input("Would you like to use VORP, Win Shares, or Both? Input one of these three options:\n")
    if avd == "vorp" or avd == "Vorp":
        avd = "VORP"
    if avd == "win shares":
        avd = "Win Shares"
    if avd == "both":
        avd == "Both"
    elif avd != "VORP" and avd != "Win Shares" and avd != "Both":
        print("Please enter a valid response")
        Get_Advanced()
    else:
        return avd


def Adjusted_or_Raw(type):
    if type == "teams":
        print("Creator Note: Adjusted values was designed with the Player rankings in mind.\n Through my testing I "
              "have noticed that raw generally leads to more accurate results.\n I wouldn't reccomend using it for "
              "Team rankings, but feel free to experiment\n")
    adj = input("Would you like to use my Adjusted advanced values or the Raw values? \n"
                "(Tip: Adjusted values will more accurately rank the least valuable players while Raw values will more "
                "accurately rank the most valuable.)\n")
    if adj == "adjusted":
        adj = "Adjusted"
        return adj
    elif adj == "raw":
        adj = "Raw"
        return adj
    elif adj != "Adjusted" and adj != "Raw":
        print("Please enter a valid response")
        Adjusted_or_Raw(type)
    else:
        return adj


def Avg_or_Tot():
    print("Would you like the list to be ranked by the total value of the players on the team or "
          "the average value per player?\n")
    user_response = input("Input Total or Average: \n")
    if user_response == "tot" or user_response == "Tot" or \
            user_response == "Total" or user_response == "total":
        user_response = "Total"
        return user_response
    elif user_response == "average" or user_response == "Average" or \
            user_response == "avg" or user_response == "Avg":
        user_response = "Average"
        return user_response
    else:
        print("Please enter a valid response.")
        Avg_or_Tot()


def parse_user_selection(user_selection):
    if user_selection == "players" or user_selection == "Players" or \
            user_selection == "player" or user_selection == "Player":
        rank_players_setup()
    elif user_selection == "team" or user_selection == "Teams" or \
            user_selection == "Team" or user_selection == "teams":
        rank_teams_setup()
    elif user_selection == "admin" or user_selection == "Admin":
        admin_settings()
    else:
        print("Please enter a valid response\n")
        go()

def rank_players_setup():
    print("Welcome to the Player Value Ranker")
    choice = Custom_or_Default()
    if choice == "Default":
        min_salary = 5000000
        rookies = "No"
        avd_metrics = "Both"
        adj_metrics = "Raw"
    else:
        min_salary = input("What is the minimum salary you would like to rank?"
                           " Enter in 1 to return all applicable contracts:\n")
        rookies = Get_Rookies()
        avd_metrics = Get_Advanced()
        adj_metrics = Adjusted_or_Raw("players")
        print("\n")
    rank_players(min_salary, rookies, avd_metrics, adj_metrics)


def rank_teams_setup():
    print("Welcome to the Team Value Ranker")
    value_type = Avg_or_Tot()
    custom_choice = Custom_or_Default()
    if custom_choice == "Default":
        min_salary = 898310
        rookies = "Yes"
        adj_metrics = "Raw"
        avd_metrics = "Raw"
    else:
        min_salary = input("What is the minimum salary you would like to rank?"
                           " Enter in 1 to return all applicable contracts:\n")
        rookies = Get_Rookies()
        avd_metrics = Get_Advanced()
        adj_metrics = Adjusted_or_Raw("teams")
        print("\n")
    rank_teams(value_type, min_salary, rookies, adj_metrics, avd_metrics)


def admin_settings():
    user_choice = input("Welcome to the Administrator Settings. \n"
                        "Would you like to rebuild the database or restart the program?(Enter Rebuild or Restart)\n")
    if user_choice == "rebuild" or user_choice == "Rebuild":
        print("Rebuilding Database")
        clear_the_collection()
        setup_the_database()
        print("Database Successfully Rebuilt. Restarting Program.")
        go()
    if user_choice == "Restart" or user_choice == "restart":
        go()


def go():
    print("Hello and welcome to the NBA Contract Value Database. This program will rank the value of NBA player \n"
          "contracts based on advanced metrics and user defined criteria. Currently, we only have the salary data \n"
          "for the 2019-2020 season. \n")
    user_selection = input("Would you like to rank the players or the teams? \n")
    parse_user_selection(user_selection)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    go()
