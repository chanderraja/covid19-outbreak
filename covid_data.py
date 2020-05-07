import pandas as pd
import datetime as dt
import os
import logging
import json
import numpy as np

def whoami( ):
    import sys
    return sys._getframe(1).f_code.co_name


# Scope
SCOPE_WORLD='Worldwide'         # worldwide scope indexed by countries
SCOPE_USA='United States'       # US scope indexed by states
SCOPE_US_COUNTIES='US Counties' # US scope indexed by counties

# Location string for overall computations
LOC_WORLD_OVERALL='Worldwide'
LOC_USA_OVERALL='US Total'

# Stats
STAT_CONFIRMED='Confirmed'
STAT_DEATHS='Deaths'
STAT_RECOVERED='Recovered'
STAT_ACTIVE='Active'

# Stat value types
VALUE_TYPE_CUMULATIVE=0
VALUE_TYPE_DAILY_DIFF=1
VALUE_TYPE_DAILY_PERCENT_CHANGE=2
VALUE_TYPE_PER_CAPITA=3
VALUE_TYPE_ONE_PER_N=4

# Data frame columns

# Daily DF columns
CSSE_DAILY_COL_FIPS='FIPS'
CSSE_DAILY_COL_PROVINCE_STATE='Province_State'
CSSE_DAILY_COL_COUNTRY_REGION='Country_Region'
CSSE_DAILY_COL_ADMIN2='Admin2'
CSSE_DAILY_COL_LATITUDE='Lat'
CSSE_DAILY_COL_LONGITUDE='Long_'
CSSE_DAILY_COL_CONFIRMED='Confirmed'
CSSE_DAILY_COL_DEATHS='Deaths'
CSSE_DAILY_COL_RECOVERED='Recovered'
CSSE_DAILY_COL_ACTIVE='Active'
CSSE_DAILY_COL_COMBINED_KEY= 'Combined_Key'
CSSE_DAILY_COL_HOVERTEXT='Hovertext'
CSSE_DAILY_COL_LAST_UPDATE='Last_Update'

CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION='Country/Region'
CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE= 'Province/State'
CSSE_TIMESERIES_COL_GLOBAL_LATITUDE='Lat'
CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE='Long'

CSSE_TIMESERIES_COL_USA_COUNTRY_REGION=CSSE_DAILY_COL_COUNTRY_REGION
CSSE_TIMESERIES_COL_USA_PROVINCE_STATE=CSSE_DAILY_COL_PROVINCE_STATE
CSSE_TIMESERIES_COL_USA_LATITUDE=CSSE_DAILY_COL_LATITUDE
CSSE_TIMESERIES_COL_USA_LONGITUDE=CSSE_DAILY_COL_LONGITUDE
CSSE_TIMESERIES_COL_USA_UID='UID'
CSSE_TIMESERIES_COL_USA_ISO2='iso2'
CSSE_TIMESERIES_COL_USA_ISO3='iso3'
CSSE_TIMESERIES_COL_USA_CODE3='code3'
CSSE_TIMESERIES_COL_USA_FIPS='FIPS'
CSSE_TIMESERIES_COL_USA_ADMIN2='Admin2'
CSSE_TIMESERIES_COL_USA_POPULATION='Population'
CSSE_TIMESERIES_COL_USA_COMBINED_KEY='Combined_Key'

# Data import config keys
IMPORT_CFG_URLS='urls'                          # key to a dict of URLs by stat
IMPORT_CFG_DROP_COLUMNS='drop_columns'          # key to a list of columns to drop from data frame
IMPORT_CFG_AGGREGATE_COLUMN='aggregate_column'  # key to a column to aggregate values by
IMPORT_CFG_RENAME_LOCATIONS='rename'            # key to a dict with key=current name and value=string to rename as
IMPORT_CFG_SET_INDEX='set_index'                # key to a column to set the data frame index to
IMPORT_CFG_POPULATION_DATA='population'         # key to a dict containing configuration to read population data
IMPORT_CFG_POPULATION_URL='url'                        # key to a dict containing configuration to read population data
IMPORT_CFG_POPULATION_LOCATION_COLUMN='location_column'     # key to a string representing the location column in the population DF
IMPORT_CFG_POPULATION_POPULATION_COLUMN='population_column' # key to a string representing the population column in the population DF
IMPORT_CFG_PER_CAPITA_MULTIPLIER='per_capita_multiplier'    # key to a value representing the per capita multiplier.
                                                            # e.g. if the multiplier is 1000, per capita stats will be in terms of
                                                            # numbers out of 1000 people

def get_stat_types():
    return [STAT_CONFIRMED, STAT_DEATHS, STAT_RECOVERED, STAT_ACTIVE]

def get_scope_types():
    return [SCOPE_WORLD, SCOPE_USA]

def get_location_overall(scope):
    if scope == SCOPE_WORLD:
        return LOC_WORLD_OVERALL
    elif scope == SCOPE_USA:
        return LOC_USA_OVERALL
    elif scope == SCOPE_US_COUNTIES:
        return LOC_USA_OVERALL
    return 'Not implemented'

def get_value_types():
    return [VALUE_TYPE_CUMULATIVE, VALUE_TYPE_DAILY_DIFF, VALUE_TYPE_DAILY_PERCENT_CHANGE]

def compute_df_per_capita(df, df_population, location_column, population_column, multiplier=1000000.0):
    df_per_capita = df.copy()
    for location in df_per_capita:
        found = df_population.query(f'{location_column} == "{location}"')[population_column]
        if found.count() == 0:
            df_per_capita.drop(location, axis=1, inplace=True)
            continue
        population = found.values[0]
        df_per_capita[location] = (df_per_capita[location] * multiplier)/population
    return df_per_capita

def compute_df_one_per_n(df, df_population, location_column, population_column):
    df_one_per_n = df.copy()
    for location in df_one_per_n:
        found = df_population.query(f'{location_column} == "{location}"')[population_column]
        if found.count() == 0:
            df_one_per_n.drop(location, axis=1, inplace=True)
            continue
        population = found.values[0]
        df_one_per_n[location] = population/df_one_per_n[location]
    df_one_per_n.replace([np.inf, -np.inf], np.nan)
    return df_one_per_n


def get_location(row):
    if CSSE_DAILY_COL_COMBINED_KEY in row.index:
        return row[CSSE_DAILY_COL_COMBINED_KEY]
    if CSSE_DAILY_COL_PROVINCE_STATE in row.index:
        if CSSE_DAILY_COL_COUNTRY_REGION in row.index:
            return row[CSSE_DAILY_COL_PROVINCE_STATE] + ', ' + row[CSSE_DAILY_COL_COUNTRY_REGION]
        else:
            return row[CSSE_DAILY_COL_PROVINCE_STATE]
    return row.name


def get_hovertext(row):
    return get_location(row) + '<br>' + \
            f'{row[CSSE_DAILY_COL_CONFIRMED]:,} confirmed' + '<br>' + \
            f'{row[CSSE_DAILY_COL_DEATHS]:,} deaths' + '<br>' + \
            f'{row[CSSE_DAILY_COL_RECOVERED]:,} recovered' + '<br>' + \
            f'{row[CSSE_DAILY_COL_ACTIVE]:,} active'


add_hovertext = lambda df: df.apply(lambda row: get_hovertext(row), axis=1)
add_location = lambda df: df.apply(lambda row: get_location(row), axis=1)


class CovidDataProcessor:
    __csse_base_url = './data/covid-19/csse_covid_19_data/'
    __csse_daily_url = __csse_base_url + 'csse_covid_19_daily_reports/'
    __csse_timeseries_url = __csse_base_url + 'csse_covid_19_time_series/'

    __geojson_world_countries_url = './data/countries.geo.json'
    __geojson_us_states_url = './data/us_states_500k_res.json'
    __geojson_us_counties_url = './data/us_counties_2010.json' #'./data/us_counties_500k_res.json'

    __population_world_url = './data/world_population.csv'
    __population_us_states_url = './data/us_states_population.csv'
    __population_us_counties_url = './data/us_counties_population.csv'

    rename_countries = {
        'Bahamas': 'The Bahamas',
        'Burma': 'Myanmar',
        'Cabo Verde': 'Cape Verde',
        'Congo (Brazzaville)': 'Republic of the Congo',
        'Congo (Kinshasa)': 'Democratic Republic of the Congo',
        'Cote d\'Ivoire': 'Ivory Coast',
        'Czechia': 'Czech Republic',
        'Guinea-Bissau': 'Guinea Bissau',
        'Holy See': 'Vatican',
        'Korea, South': 'South Korea',
        'North Macedonia': 'Macedonia',
        'Eswatini': 'Swaziland',
        'Timor-Leste': 'East Timor',
        'Taiwan*': 'Taiwan',
        'Tanzania': 'United Republic of Tanzania',
        'US': 'United States of America',
        'West Bank and Gaza': 'West Bank'
    }

    daily_aggregation_functions = {
        CSSE_DAILY_COL_CONFIRMED: 'sum',
        CSSE_DAILY_COL_DEATHS: 'sum',
        CSSE_DAILY_COL_RECOVERED: 'sum',
        CSSE_DAILY_COL_ACTIVE: 'sum',
        CSSE_DAILY_COL_LATITUDE: 'mean',
        CSSE_DAILY_COL_LONGITUDE: 'mean',
        CSSE_DAILY_COL_LAST_UPDATE: 'max'
    }

    csse_daily_stat_to_col_map = {
        STAT_CONFIRMED: CSSE_DAILY_COL_CONFIRMED,
        STAT_DEATHS: CSSE_DAILY_COL_DEATHS,
        STAT_ACTIVE: CSSE_DAILY_COL_ACTIVE,
        STAT_RECOVERED: CSSE_DAILY_COL_RECOVERED
    }

    scope_to_totals_map = {}

    time_series_by_location_lookup = {
        SCOPE_WORLD: {},
        SCOPE_USA: {},
        SCOPE_US_COUNTIES: {}
    }

    population_data_lookup = {
    }
    time_series_data_config = {
        SCOPE_WORLD: {
            IMPORT_CFG_POPULATION_DATA: {
                IMPORT_CFG_POPULATION_URL: __population_world_url,
                IMPORT_CFG_POPULATION_LOCATION_COLUMN: 'name',
                IMPORT_CFG_POPULATION_POPULATION_COLUMN: 'population',
            },
            IMPORT_CFG_URLS: {
                STAT_CONFIRMED: __csse_timeseries_url + 'time_series_covid19_confirmed_global.csv',
                STAT_DEATHS: __csse_timeseries_url + 'time_series_covid19_deaths_global.csv',
                STAT_RECOVERED: __csse_timeseries_url + 'time_series_covid19_recovered_global.csv'
            },
            IMPORT_CFG_DROP_COLUMNS: [
                CSSE_TIMESERIES_COL_GLOBAL_PROVINCE_STATE,
                CSSE_TIMESERIES_COL_GLOBAL_LATITUDE,
                CSSE_TIMESERIES_COL_GLOBAL_LONGITUDE,
            ],
            IMPORT_CFG_AGGREGATE_COLUMN: CSSE_TIMESERIES_COL_GLOBAL_COUNTRY_REGION,
            IMPORT_CFG_RENAME_LOCATIONS: rename_countries,
            IMPORT_CFG_PER_CAPITA_MULTIPLIER: 100000.0
        },

        SCOPE_USA: {
            IMPORT_CFG_POPULATION_DATA: {
                IMPORT_CFG_POPULATION_URL: __population_us_states_url,
                IMPORT_CFG_POPULATION_LOCATION_COLUMN: 'state',
                IMPORT_CFG_POPULATION_POPULATION_COLUMN: 'population',
            },
            IMPORT_CFG_URLS: {
                STAT_CONFIRMED: __csse_timeseries_url + 'time_series_covid19_confirmed_US.csv',
                STAT_DEATHS: __csse_timeseries_url + 'time_series_covid19_deaths_US.csv',
            },
            IMPORT_CFG_DROP_COLUMNS: [
                CSSE_TIMESERIES_COL_USA_COUNTRY_REGION,
                CSSE_TIMESERIES_COL_USA_LATITUDE,
                CSSE_TIMESERIES_COL_USA_LONGITUDE,
                CSSE_TIMESERIES_COL_USA_UID,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_ISO3,
                CSSE_TIMESERIES_COL_USA_CODE3,
                CSSE_TIMESERIES_COL_USA_FIPS,
                CSSE_TIMESERIES_COL_USA_POPULATION
            ],
            IMPORT_CFG_AGGREGATE_COLUMN: CSSE_TIMESERIES_COL_USA_PROVINCE_STATE,
            IMPORT_CFG_PER_CAPITA_MULTIPLIER: 10000.0
        },

        SCOPE_US_COUNTIES: {
            IMPORT_CFG_POPULATION_DATA: {
                IMPORT_CFG_POPULATION_URL: __population_us_counties_url,
                IMPORT_CFG_POPULATION_LOCATION_COLUMN: 'Combined_Key',
                IMPORT_CFG_POPULATION_POPULATION_COLUMN: 'Population',
            },
            IMPORT_CFG_URLS: {
                STAT_CONFIRMED: __csse_timeseries_url + 'time_series_covid19_confirmed_US.csv',
                STAT_DEATHS: __csse_timeseries_url + 'time_series_covid19_deaths_US.csv',
            },
            IMPORT_CFG_DROP_COLUMNS: [
                CSSE_TIMESERIES_COL_USA_COUNTRY_REGION,
                CSSE_TIMESERIES_COL_USA_PROVINCE_STATE,
                CSSE_TIMESERIES_COL_USA_LATITUDE,
                CSSE_TIMESERIES_COL_USA_LONGITUDE,
                CSSE_TIMESERIES_COL_USA_UID,
                CSSE_TIMESERIES_COL_USA_ISO2,
                CSSE_TIMESERIES_COL_USA_ISO3,
                CSSE_TIMESERIES_COL_USA_ADMIN2,
                CSSE_TIMESERIES_COL_USA_CODE3,
                CSSE_TIMESERIES_COL_USA_FIPS,
                CSSE_TIMESERIES_COL_USA_POPULATION
            ],
            IMPORT_CFG_SET_INDEX: CSSE_TIMESERIES_COL_USA_COMBINED_KEY,
            IMPORT_CFG_PER_CAPITA_MULTIPLIER: 1000.0
        }
    }

    def __init_logger(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        # add the handlers to logger
        self.logger.addHandler(ch)
        self.time_series_by_location_lookup = dict()
        self.time_series_by_overall_lookup = dict()
        for scope in get_scope_types():
            self.time_series_by_location_lookup[scope] = dict()
            self.time_series_by_overall_lookup[scope] = dict()
            for stat in get_stat_types():
                self.time_series_by_location_lookup[scope][stat] = dict()
                self.time_series_by_overall_lookup[scope][stat] = dict()

    def __read_world_countries_geojson(self):
        with open(self.__geojson_world_countries_url) as f:
            self.geojson_world_countries = json.load(f)

    def __read_us_counties_geojson(self):
        with open(self.__geojson_us_counties_url) as f:
            self.geojson_us_counties = json.load(f)
            for feat in self.geojson_us_counties['features']:
                state_fips = feat['properties']['STATE']
                county_fips = feat['properties']['COUNTY']
                feat['id'] = state_fips + county_fips

    def __read_us_states_geojson(self):
        with open(self.__geojson_us_states_url) as f:
            self.geojson_us_states = json.load(f)

    def __check_countries_in_province_field(self, df):
        geojson = self.geojson_world_countries
        for feat in geojson['features']:
            country = feat['properties']['name']
            if not df[CSSE_DAILY_COL_COUNTRY_REGION].isin([country]).any():
                # is it in province field?
                if df[CSSE_DAILY_COL_PROVINCE_STATE].isin([country]).any():
                    matching_rows = df[df[CSSE_DAILY_COL_PROVINCE_STATE] == country]
                    if not matching_rows.empty:
                        self.logger.warning(f'{country} found in state/province field of datastet, copying to country field')
                        matching_rows[CSSE_DAILY_COL_COUNTRY_REGION].iloc[0] = country
                    continue
                if self.logger is not None:
                    self.logger.warning(f'{country} not found in dataset')
                continue

    def __read_csse_daily_report(self):
        today = dt.datetime.today()
        csse_daily_csv = ''
        for i in range(0, 10):
            date_str = f'{today - dt.timedelta(days=i):%m-%d-%Y}'
            csse_daily_csv = self.__csse_daily_url + date_str + '.csv'
            if os.path.isfile(csse_daily_csv):
                break

        self.logger.info('Reading f{csse_daily_csv}...')
        df_daily_global = pd.read_csv(csse_daily_csv, dtype={CSSE_DAILY_COL_FIPS: str})
        self.__check_countries_in_province_field(df_daily_global)

        # make a world countries data frame
        self.logger.info('processing daily global data...')
        self.df_daily_world = df_daily_global.drop(
            columns=[CSSE_DAILY_COL_FIPS, CSSE_DAILY_COL_PROVINCE_STATE, CSSE_DAILY_COL_ADMIN2, CSSE_DAILY_COL_COMBINED_KEY])
        self.df_daily_world = self.df_daily_world.groupby(
            self.df_daily_world[CSSE_DAILY_COL_COUNTRY_REGION]).aggregate(self.daily_aggregation_functions)
        self.df_daily_world.rename(self.rename_countries, inplace=True)
        self.df_daily_world.sort_index(inplace=True)
        self.df_daily_world[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_world)

        # compute global totals
        self.logger.info('computing global daily totals...')
        self.global_totals = self.df_daily_world.aggregate(self.daily_aggregation_functions)
        self.scope_to_totals_map[SCOPE_WORLD] = self.global_totals

        # make a US counties dataframe
        self.logger.info('Deriving data for US counties...')
        self.df_daily_us_counties = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        # drop rows with NaN in FIPS column
        self.df_daily_us_counties = self.df_daily_us_counties[self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].notna()]
        self.df_daily_us_counties[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_us_counties)
        self.df_daily_us_counties[CSSE_DAILY_COL_FIPS] = self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].astype(str)
        self.df_daily_us_counties[CSSE_DAILY_COL_FIPS] = self.df_daily_us_counties[CSSE_DAILY_COL_FIPS].apply('{:0>5}'.format)
        self.df_daily_us_counties.set_index(keys=CSSE_DAILY_COL_FIPS, inplace=True)

        # make a US states dataframe
        self.logger.info('Deriving data for US states...')
        self.df_daily_us_states = df_daily_global[df_daily_global[CSSE_DAILY_COL_COUNTRY_REGION]=='US']
        self.df_daily_us_states.drop(columns=[CSSE_DAILY_COL_FIPS])
        self.df_daily_us_states = \
            self.df_daily_us_states.groupby(self.df_daily_us_states[CSSE_DAILY_COL_PROVINCE_STATE]).aggregate('sum')
        self.df_daily_us_states[CSSE_DAILY_COL_HOVERTEXT] = add_hovertext(self.df_daily_us_states)

        # compute us totals
        self.logger.info('computing US daily totals...')
        self.usa_totals = self.df_daily_us_counties.aggregate(self.daily_aggregation_functions)
        self.scope_to_totals_map[SCOPE_USA] = self.usa_totals
        self.scope_to_totals_map[SCOPE_US_COUNTIES] = self.usa_totals


    def __get_csse_time_series_data(self, url, set_index=None, sum_index='Total',
                                    drop_columns=None,
                                    aggregate_column=None,
                                    logtext=None,
                                    rename_locations=None):
        if logtext is not None:
            self.logger.info(f'Reading {logtext} data from {url}...')
        df = pd.read_csv(url)

        if set_index is not None:
            df.set_index(keys=set_index, inplace=True)
        if drop_columns is not None:
            self.logger.info(f'Dropping unwanted columns...')
            df.drop(columns=drop_columns, inplace=True, errors='ignore')
        if aggregate_column is not None:
            df = df.groupby(df[aggregate_column]).aggregate('sum')
        if rename_locations is not None:
            df.rename(index=rename_locations, inplace=True)
            df.sort_index(inplace=True)
        sum = df.aggregate('sum')
        df_sum = pd.DataFrame([sum], index=[sum_index])
        df_sum = df_sum.transpose()
        df_sum.index = pd.to_datetime(df_sum.index)
        #df = pd.concat([df_sum, df], sort=False)
        df1_transposed = df.transpose()
        df1_transposed.index = pd.to_datetime(df1_transposed.index)
        return df1_transposed, df_sum

    def compute_df_for_value_types(self, df, df_pop=None, loc_column=None, pop_column=None, multiplier=None):
        """
        Compute data frames for all supported value types from a time series dataframe and return as a dict indexed by
        value type
        :param df: time series dataframe
        :return: dict of data frames indexed by value types
        """
        d = dict()
        d[VALUE_TYPE_CUMULATIVE] = df
        d[VALUE_TYPE_DAILY_DIFF] = df.diff()
        df1 = df.pct_change() * 100
        df1 = df1.replace([np.inf, -np.inf], np.nan)
        d[VALUE_TYPE_DAILY_PERCENT_CHANGE] = df1
        if df_pop is not None:
            d[VALUE_TYPE_PER_CAPITA] = compute_df_per_capita(df, df_pop,
                                  location_column=loc_column,
                                  population_column=pop_column,
                                  multiplier=multiplier)
            d[VALUE_TYPE_ONE_PER_N] = compute_df_one_per_n(df, df_pop,
                                  location_column=loc_column,
                                  population_column=pop_column)
        return d

    def __read_time_series_data(self):
        cfg = self.time_series_data_config
        for scope in get_scope_types():
            log_prefix = f'{whoami()}: scope={scope}: '
            cfg_scope = cfg.get(scope)
            if cfg_scope is None:
                self.logger.warning(f'{log_prefix}No data config found for this scope, skipping...')
                continue
            popdata_loc_column = 'name'
            popdata_cfg = cfg_scope.get(IMPORT_CFG_POPULATION_DATA)
            if popdata_cfg is not None:
                pop_data_url = popdata_cfg[IMPORT_CFG_POPULATION_URL]
                popdata_loc_column = popdata_cfg[IMPORT_CFG_POPULATION_LOCATION_COLUMN]
                popdata_pop_column = popdata_cfg[IMPORT_CFG_POPULATION_POPULATION_COLUMN]
                self.logger.info(f'reading {scope} population data from {pop_data_url}...')
                df_pop = pd.read_csv(pop_data_url)
                df_pop.loc['Total'] = df_pop.sum(numeric_only=True, axis=0)
                df_pop.at['Total', popdata_loc_column] = get_location_overall(scope)

            urls = cfg_scope.get(IMPORT_CFG_URLS)
            if urls is None:
                self.logger.error(f'{log_prefix}No URL section found in config, skipping...')
                continue
            set_index = cfg_scope.get(IMPORT_CFG_SET_INDEX)
            drop_columns = cfg_scope.get(IMPORT_CFG_DROP_COLUMNS)
            aggregate_column = cfg_scope.get(IMPORT_CFG_AGGREGATE_COLUMN)
            rename_locations = cfg_scope.get(IMPORT_CFG_RENAME_LOCATIONS)
            per_capita_multiplier = 100000.0
            if cfg_scope.get(IMPORT_CFG_PER_CAPITA_MULTIPLIER) is not None:
                per_capita_multiplier = cfg_scope[IMPORT_CFG_PER_CAPITA_MULTIPLIER]
            for stat in get_stat_types():
                log_prefix2 = log_prefix + f'stat = {stat}: '
                url = urls.get(stat)
                if url is None:
                    self.logger.error(f'{log_prefix2}No URL found for this statistic, skipping...')
                    continue
                # read data file into a data frame
                self.logger.info(f'scope={scope} stat={stat}: Reading raw data from {url}...')
                df = pd.read_csv(url)

                if set_index is not None:
                    self.logger.info(f'{log_prefix2}Setting index to {set_index}')
                    df.set_index(keys=set_index, inplace=True)
                if drop_columns is not None:
                    self.logger.info(f'{log_prefix2}Dropping unwanted columns - {drop_columns}...')
                    df.drop(columns=drop_columns, inplace=True, errors='ignore')
                if aggregate_column is not None:
                    self.logger.info(f'{log_prefix2}Aggregating values by column {aggregate_column}...')
                    df = df.groupby(df[aggregate_column]).aggregate('sum')
                if rename_locations is not None:
                    self.logger.info(f'{log_prefix2}Renaming locations and sorting by location names...')
                    df.rename(index=rename_locations, inplace=True)
                    df.sort_index(inplace=True)
                sum = df.aggregate('sum')
                df_sum = pd.DataFrame([sum], index=[get_location_overall(scope)])
                df_sum = df_sum.transpose()
                df_sum.index = pd.to_datetime(df_sum.index)
                # df = pd.concat([df_sum, df], sort=False)
                df1_transposed = df.transpose()
                df1_transposed.index = pd.to_datetime(df1_transposed.index)

                self.time_series_by_location_lookup[scope][stat] = \
                    self.compute_df_for_value_types(df1_transposed,
                                                    df_pop=df_pop,
                                                    loc_column=popdata_loc_column,
                                                    pop_column=popdata_pop_column,
                                                    multiplier=per_capita_multiplier)
                self.time_series_by_overall_lookup[scope][stat]= \
                    self.compute_df_for_value_types(df_sum,
                                                    df_pop=df_pop,
                                                    loc_column=popdata_loc_column,
                                                    pop_column=popdata_pop_column,
                                                    multiplier=per_capita_multiplier)
        pass

    def __read_csse_time_series_reports(self):
        self.__read_time_series_data()

    def __check_name_lists(self, list1, list1_name, list2, list2_name):
        print(f'Comparing {list1_name} with {list2_name}')
        intersection = sorted(list(set(list1) & set(list2)))
        print(f'intersection = {intersection}')
        list1_only = sorted(list(set(list1) - set(list2)))
        print(f'only in {list1_name} = {list1_only}')
        list2_only = sorted(list(set(list2) - set(list1)))
        print(f'only in {list2_name} = {list2_only}')

    def __init__(self, *args, **kwargs):
        self.__init_logger()
        self.__read_world_countries_geojson()
        self.__read_us_states_geojson()
        self.__read_us_counties_geojson()
        self.__read_csse_daily_report()
        self.__read_time_series_data()
        self.__read_csse_time_series_reports()
        #self.__check_name_lists(list(self.population_data_lookup[SCOPE_WORLD]['name']), 'pop_world', list(self.df_confirmed_by_date_world.columns), 'df_world')
        #self.__check_name_lists(list(self.population_data_lookup[SCOPE_WORLD]['state']), 'pop_us_states', list(self.df_confirmed_by_date_usa.columns), 'df_us_states')
        #self.__check_name_lists(list(self.population_data_lookup[SCOPE_WORLD]['Combined_Key']), 'pop_us_counties', list(self.df_confirmed_by_date_us_counties.columns), 'df_us_counties')
        pass

    def get_geojson(self, scope):
        """
        :return: parsed geoJSON based on scope
        """
        if scope == SCOPE_WORLD:
            return self.geojson_world_countries
        elif scope == SCOPE_USA:
            return self.geojson_us_states
        elif scope == SCOPE_US_COUNTIES:
            return self.geojson_us_counties
        else:
            return None

    def get_stat_by_date_df(self, scope, stat, value_type=VALUE_TYPE_CUMULATIVE, overall=False):
        """
        return dataframe containing stat by date
        :param scope: SCOPE_WORLD or other defined scope
        :param stat: stat to return in dataframe (STAT_CONFIRMED, STAT_DEATHS etc)
        :param: value_type: e.g. VALUE_TYPE_CUMULATIVE, VALUE_TYPE_DAILY_CHANGE etc
        :param: overall: if true get stats for overall location given by scope else get stats broken down by sub locations
        :return: dataframe containing requested stats per location (defined by scope) by date
        """
        lookup = self.time_series_by_location_lookup if overall is False else self.time_series_by_overall_lookup
        if scope not in lookup:
            self.logger.error(f'No data available for scope={scope}')
            return None
        stat_lookup = lookup[scope]
        if stat not in stat_lookup:
            self.logger.error(f'No data found for stat={stat} under scope={scope}')
            return None
        value_type_lookup = stat_lookup[stat]
        if value_type not in value_type_lookup:
            self.logger.error(f'No data found for stat={stat}, scope={scope}, value_type={value_type}')
            return None
        df = value_type_lookup[value_type]
        return df

    def get_latest_stat(self, stat, scope, loc=None):
        """

        :param scope:
        :param location:
        :return:
        """
        df = self.get_stat_by_date_df(scope, stat, value_type=VALUE_TYPE_CUMULATIVE, overall=(loc is None))
        df_diff = self.get_stat_by_date_df(scope, stat, value_type=VALUE_TYPE_DAILY_DIFF, overall=(loc is None))
        df_pct_change = self.get_stat_by_date_df(scope, stat, value_type=VALUE_TYPE_DAILY_PERCENT_CHANGE, overall=(loc is None))
        df_per_capita = self.get_stat_by_date_df(scope, stat, value_type=VALUE_TYPE_PER_CAPITA, overall=(loc is None))
        df_one_per_n = self.get_stat_by_date_df(scope, stat, value_type=VALUE_TYPE_ONE_PER_N, overall=(loc is None))
        latest_date = df.index.max()
        if loc is None:
            loc = get_location_overall(scope)
        value = df.loc[latest_date, loc]
        pct_change = df_pct_change.loc[latest_date, loc]
        diff = df_diff.loc[latest_date, loc]
        per_capita = df_per_capita.loc[latest_date, loc]
        one_per_n = df_one_per_n.loc[latest_date, loc]
        return value, diff, pct_change, per_capita, one_per_n


    def get_df_daily_report(self, scope):
        """
        Get the data frame for the Covid-19 daily report indexed by locations depending on scope
        :param scope: SCOPE_WORLD or SCOPE_USA
        :return: data frame containing daily reports of confirmed cases deaths and recovered cases
        which are obtained from the columns CSSE_DAILY_COL_CONFIRMED, CSSE_DAILY_COL_DEATHS,
        CSSE_DAILY_COL_RECOVERED and CSSE_DAILY_COL_ACTIVE. Also CSSE_DAILY_COL_LATITUDE and
        CSSE_DAILY_COL_LONGITUDE provides the central lat and long coordinates for the location
        TODO: add specifics for world and US county data frames
        """
        if scope == SCOPE_WORLD:
            return self.df_daily_world
        elif scope == SCOPE_USA:
            return self.df_daily_us_states
        elif scope == SCOPE_US_COUNTIES:
            return self.df_daily_us_counties
        else:
            return None

    def get_all_locations(self, scope, stat=STAT_CONFIRMED):
        """
        Get a list of all locations from which we have data for the specified scope
        :param scope: SCOPE_WORLD or SCOPE_USA
        :param stat: optional stat to sepecify which dataframe to get location data from
        :return: list of locations specific to scope
        """
        df = self.get_stat_by_date_df(scope, stat=stat)
        return df.columns

    def get_top_locations(self, scope, stat, value_type=VALUE_TYPE_CUMULATIVE, n=10):
        df = self.get_stat_by_date_df(scope, stat, value_type=value_type)
        latest_date = df.index.max()
        latest_series = df.loc[latest_date]
        return latest_series.nlargest(n=n)

    def get_bottom_locations(self, scope, stat, n=10):
        df = self.get_df_daily_report(scope)
        df1 = df.dropna()
        df1 = df1.nsmallest(n=n, columns=[stat])

        df1.set_index(add_location(df1), inplace=True)
        return df1

