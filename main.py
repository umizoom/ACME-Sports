#!/usr/bin/env python3
import argparse
import sys
import requests
import logging
import json
from typing import List
from datetime import datetime

# Constants

LEAGUE = 'NFL'


class ApiHandler:
    """
    Used to interact with the API endpoints
    """

    def __init__(self, api_key: str):
        """
        Constructor for the API handler
        :param api_key: API key, sourced from the command line
        """
        self.api_url = 'https://delivery.chalk247.com'
        self.api_key = api_key

    def get_team_rankings(self) -> requests.Response:
        """
        Makes a GET request to the team_rankings endpoint.
        :return: request.Response
        """
        url = f'{self.api_url}/team_rankings/{LEAGUE}?api_key={self.api_key}'
        team_ranking_response = requests.get(url)
        if team_ranking_response.status_code >= 400:
            logging.error(f'Status code {str(team_ranking_response.status_code)} received from /team_rankings '
                          f'endpoint with message {team_ranking_response.text}')
            exit(1)
        return team_ranking_response

    def get_score_board(self, start_date, end_date) -> requests.Response:
        """
        Makes a GET request to the scoreboard endpoint
        :param start_date: The start date to calculate scoreboard from
        :param end_date: The end date to calculate scoreboard from
        :return: request.Response
        """
        url = f'{self.api_url}/scoreboard/{LEAGUE}/{start_date}/{end_date}?api_key={self.api_key}'
        scoreboard_response = requests.get(url)
        # Use the API to handle bad inputs, such as reverse start and end dates or start and end dates greater than 7
        # days
        if scoreboard_response.status_code >= 400:
            logging.error(f'Status code {str(scoreboard_response.status_code)} received from /scoreboard endpoint '
                          f'with message {scoreboard_response.text}')
            exit(1)
        return scoreboard_response


def parse_score_board(start_date, end_date, api_helper: ApiHandler) -> List[dict]:
    """
    Parses the data from get_score_board method.
    :param start_date: The start date to calculate scoreboard from
    :param end_date: The end date to calculate scoreboard from
    :param api_helper: API helper object.
    :return:
    """
    score_rankings_raw = api_helper.get_score_board(start_date=start_date, end_date=end_date).json()
    list_of_score_rankings = []
    for outer_key in score_rankings_raw['results'].keys():
        if score_rankings_raw['results'][outer_key]:
            inner_keys = score_rankings_raw['results'][outer_key]['data'].keys()
            for inner_key in inner_keys:
                new_score_rankings = dict()
                new_score_rankings['event_id'] = score_rankings_raw['results'][outer_key]['data'][inner_key]['event_id']
                new_score_rankings['event_date'] = parse_date(
                    score_rankings_raw['results'][outer_key]['data'][inner_key]['event_date'])
                new_score_rankings['event_time'] = parse_time(
                    score_rankings_raw['results'][outer_key]['data'][inner_key]['event_date'])
                new_score_rankings['away_team_id'] = score_rankings_raw['results'][outer_key]['data'][inner_key][
                    'away_team_id']
                new_score_rankings['away_nick_name'] = score_rankings_raw['results'][outer_key]['data'][inner_key][
                    'away_nick_name']
                new_score_rankings['away_city'] = \
                    score_rankings_raw['results'][outer_key]['data'][inner_key]['away_city']
                new_score_rankings['away_rank'] = None
                new_score_rankings['away_rank_points'] = None
                new_score_rankings['home_team_id'] = score_rankings_raw['results'][outer_key]['data'][inner_key][
                    'home_team_id']
                new_score_rankings['home_nick_name'] = score_rankings_raw['results'][outer_key]['data'][inner_key][
                    'home_nick_name']
                new_score_rankings['home_city'] = \
                    score_rankings_raw['results'][outer_key]['data'][inner_key]['home_city']
                new_score_rankings['home_rank'] = None
                new_score_rankings['home_rank_points'] = None
                list_of_score_rankings.append(new_score_rankings)
    return list_of_score_rankings


def parse_team_rankings(score_board_response, api_helper) -> List[dict]:
    """
    Parses data from team_ranking method, updates the data structure returned from the parse_score_board method
    :param score_board_response: Response from scoreboard parser
    :param api_helper: API hadler method
    :return: List of dictionaries
    """

    team_rankings_raw = api_helper.get_team_rankings().json()
    for team_rank in team_rankings_raw['results']['data']:
        for response in score_board_response:
            # Team_id from the /team_rankings end point matches the home_team_id and the away_team_id from the
            # /score_board endpoint. Using these IDs to merge data between the 2 endpoints.
            # Using f strings to round adjusted_points to 2 decimal places
            if team_rank['team_id'] == response['home_team_id']:
                response['home_rank'] = team_rank['rank']
                response['home_rank_points'] = f"{float(team_rank['adjusted_points']):.2f}"
            if team_rank['team_id'] == response['away_team_id']:
                response['away_rank'] = team_rank['rank']
                response['away_rank_points'] = f"{float(team_rank['adjusted_points']):.2f}"
    return score_board_response


def parse_time(date_time_str: str) -> str:
    """
    Returns time in HH:MM format
    :param date_time_str: date and time string to be parsed.
    :return: HH:MM
    """
    date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
    return date_time_obj.strftime('%H:%M')


def parse_date(date_time_str: str) -> str:
    """
    Returns date in DD-MM-YYYY format
    :param date_time_str:
    :return: DD-MM-YYYY
    """
    date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
    return date_time_obj.strftime('%d-%m-%Y')


def entry_point(argv=None):
    """
    Entry point for script. Creates an arg_parser.
    Prints response in JSON, If response from parse_team_rankings is empty, informs user that
    the response was empty.
    :param argv: Used too pass in arguments when program is not called from command line. Such as in tests.
    :return: None
    """
    # create arg parser
    parser = argparse.ArgumentParser(prog='main', description='List NFL data gathered from remote API')

    parser.add_argument('-api_key', required=True, action='store', dest='API_KEY',
                        help='API Key used to authenticate to the server')
    parser.add_argument('-start_date', required=True, action='store', dest='START_DATE',
                        help='Start date used to narrow down the scoreboard ')
    parser.add_argument('-end_date', required=True, action='store', dest='END_DATE',
                        help='End date used to narrow down the scoreboard')
    parser.add_argument('-v', '-version', action='version', version='1.0.0')
    args = parser.parse_args(argv)

    # create api handler object
    api_helper = ApiHandler(api_key=args.API_KEY)
    # call scoreboard parser method with start and end dates taken from command line
    score_board_response = parse_score_board(start_date=args.START_DATE, end_date=args.END_DATE, api_helper=api_helper)
    # call team rankings, takes data returned by the parse_score_board method
    formatted_output = parse_team_rankings(score_board_response=score_board_response, api_helper=api_helper)
    if formatted_output:
        print(json.dumps(formatted_output, indent=4))
    else:
        print('Response was empty, please try another start and end time')


if __name__ == "__main__":
    sys.exit(entry_point())
