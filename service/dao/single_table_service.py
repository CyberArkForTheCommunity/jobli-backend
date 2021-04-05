import logging
from abc import abstractmethod
from typing import Dict, List, Optional

import boto3
from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key, Attr

from service.dao.constants import EnvVarNames
from service.dao.utils import get_env_or_raise, TimeUtils

logger = Logger()

DATA_DELIMITER = "#"

class SingleTableRecord(object):
    def __init__(self):
        self.pk = None
        self.sk = None
        self.gsi1Pk = None
        self.gsi1Sk = None

    @abstractmethod
    def produce_pk(self) -> str:
        pass

    @abstractmethod
    def produce_sk(self) -> str:
        pass

    @abstractmethod
    def produce_gsi1_sk(self) -> str:
        pass

    @abstractmethod
    def produce_gsi1_pk(self) -> str:
        pass

    @abstractmethod
    def as_dict(self) -> Dict:
        pass


_LAST_UPDATE_TIME = "lastUpdateTime"
_CREATION_TIME = "creationTime"
_CREATED_BY = "createdBy"
_LAST_UPDATE_BY = "lastUpdatedBy"
_VERSION = "version"


class _SingleTableService:

    def __init__(self):
        self.__initialized: bool = False
        self.__dynamodb_resource = None
        self.__table_name: str = ""
        self.__table = None
        self.__GSI_1_NAME = None

    def __init(self) -> None:
        if self.__initialized:
            return

        self.__GSI_1_NAME = "GSI1" # get_env_or_raise(EnvVarNames.DYNAMO_GSI_1)
        self.__PK: str = "pk" # get_env_or_raise(EnvVarNames.TABLE_PK)  # "pk"
        self.__SK: str = "sk" # get_env_or_raise(EnvVarNames.TABLE_SK)  # "sk"
        self.__GSI1_PK: str = "gsi1Pk" # get_env_or_raise(EnvVarNames.TABLE_GSI_1_PK)  # "gsi1Pk"
        self.__GSI1_SK: str = "gsi1Sk" # get_env_or_raise(EnvVarNames.TABLE_GSI_1_SK)  # "gsi1Sk"
        # self.__region = get_env_or_raise(EnvVarNames.AWS_REGION)
        # logger.debug(f"Region is: {self.__region}")


        self.__dynamodb_resource = boto3.resource('dynamodb')
        self.__table_name = get_env_or_raise(EnvVarNames.TABLE_NAME)

        logger.debug(f"Table name set to: '{self.__table_name}'")
        self.__table = self.__dynamodb_resource.Table(self.__table_name)

        self.__initialized = True

    def find_by_pk_and_sk_begins_with(self, pk: str, sk_starts_with: str) -> List[Dict]:
        self.__init()

        query_response = self.__table.query(
            KeyConditionExpression=Key(self.__PK).eq(pk) & Key(self.__SK).begins_with(
                sk_starts_with),
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL'
        )

        items = query_response["Items"]
        last_evaluate_key = query_response.get('LastEvaluatedKey')
        logger.debug(f"Query resulted with '{len(items)}' items, last_evaluate_key: '{last_evaluate_key}'")

        while last_evaluate_key:
            logger.info(f"Continue to query for more items, last_evaluate_key: '{last_evaluate_key}'")
            query_response = self.__table.query(
                KeyConditionExpression=Key(self.__PK).eq(pk) & Key(self.__SK).begins_with(
                    sk_starts_with),
                Select='ALL_ATTRIBUTES',
                ReturnConsumedCapacity='TOTAL',
                ExclusiveStartKey=last_evaluate_key
            )

            items.extend(query_response["Items"])
            last_evaluate_key = query_response.get('LastEvaluatedKey')
            logger.debug(f"Current items count: '{len(items)}'"
                         f", last_evaluate_key: '{last_evaluate_key}'")

        if items:
            self.__clean_single_table_indices_attributes(items)
            return items
        else:
            return []

    def find_by_pk_and_sk(self, pk: str, sk: str) -> Optional[Dict]:
        self.__init()
        get_item_response = self.__table.get_item(
            Key={
                self.__PK: pk,
                self.__SK: sk
            }
        )
        if 'Item' not in get_item_response:
            return None
        else:
            item = get_item_response['Item']
            self.__clean_single_table_indices_attributes([item])
            return item

    ###################################################################################################################
    # TODO: This method was changed to support bulk read but was not tested
    ###################################################################################################################
    def find_all_by_gsi1pk_and_gsi1sk_begins_with(self, gsi_1_pk: str, gsi1sk_starts_with: str) -> Optional[List[Dict]]:
        self.__init()
        # if not gsi1sk_starts_with:
        #     gsi1sk_starts_with = ""

        if gsi1sk_starts_with:
            condition = Key(self.__GSI1_PK).eq(gsi_1_pk) & Key(self.__GSI1_SK).begins_with(gsi1sk_starts_with)
        else:
            condition = Key(self.__GSI1_PK).eq(gsi_1_pk)

        query_response = self.__table.query(
            # "sk" is the range key for the main index, and is the partition key for GSI_1
            IndexName=self.__GSI_1_NAME,
            KeyConditionExpression=condition,
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL'
        )

        items = query_response["Items"]
        last_evaluate_key = query_response.get('LastEvaluatedKey')
        logger.debug(f"Query resulted with '{len(items)}' items, last_evaluate_key: '{last_evaluate_key}'")

        while last_evaluate_key:
            logger.info(f"Continue to query for more items, last_evaluate_key: '{last_evaluate_key}'")

            query_response = self.__table.query(
                # "sk" is the range key for the main index, and is the partition key for GSI_1
                IndexName=self.__GSI_1_NAME,
                KeyConditionExpression=condition,
                Select='ALL_ATTRIBUTES',
                ReturnConsumedCapacity='TOTAL',
                ExclusiveStartKey=last_evaluate_key,
            )

            items.extend(query_response["Items"])
            last_evaluate_key = query_response.get('LastEvaluatedKey')
            logger.debug(f"Current items count: '{len(items)}'"
                         f", last_evaluate_key: '{last_evaluate_key}'")

        if items:
            self.__clean_single_table_indices_attributes(items)
            return items
        else:
            return None

    def find_all_by_pk_starts_with(self, pk_prefix: str) -> List[Dict]:
        self.__init()

        filter_expression = Key(self.__PK).begins_with(pk_prefix)
        query_response = self.__table.scan(
            FilterExpression=filter_expression,
            Select='ALL_ATTRIBUTES',
            ReturnConsumedCapacity='TOTAL'
        )

        items = query_response["Items"]
        last_evaluate_key = query_response.get('LastEvaluatedKey')
        logger.debug(f"Query resulted with '{len(items)}' items, last_evaluate_key: '{last_evaluate_key}'")

        while last_evaluate_key:
            logger.info(f"Continue to query for more items, last_evaluate_key: '{last_evaluate_key}'")

            query_response = self.__table.query(
                FilterExpression=filter_expression,
                Select='ALL_ATTRIBUTES',
                ReturnConsumedCapacity='TOTAL',
                ExclusiveStartKey=last_evaluate_key
            )

            items.extend(query_response["Items"])
            last_evaluate_key = query_response.get('LastEvaluatedKey')
            logger.debug(f"Current items count: '{len(items)}'"
                         f", last_evaluate_key: '{last_evaluate_key}'")

        if items:
            self.__clean_single_table_indices_attributes(items)
            return items
        else:
            return []

    def scan_by_filter(self, filter_expression) -> List[Dict]:
        self.__init()

        scan_response = self.__table.scan(
            FilterExpression=filter_expression
        )
        files = scan_response['Items']

        # If the total number of scanned items exceeds the maximum dataset size limit of 1 MB, the scan stops and
        # results are returned to the user as a LastEvaluatedKey value to continue the scan in a subsequent operation
        while scan_response.get('LastEvaluatedKey'):
            scan_response = self.__table.scan(
                ExclusiveStartKey=scan_response.get('LastEvaluatedKey'),
                FilterExpression=filter_expression
            )
            files.extend(scan_response['Items'])

        self.__clean_single_table_indices_attributes(files)
        return files

    # need to add update item and remove item
    def create_item(self, record: SingleTableRecord, user: str = None) -> Dict:

        self.__init()

        # if not user:
        #     user = SessionContext.get_user_name()

        now = TimeUtils.get_time_iso8601()
        record_dict = record.as_dict()

        # set mandatory index keys
        self.__set_index_keys(record, record_dict)

        record_dict[_CREATION_TIME] = now
        record_dict[_LAST_UPDATE_TIME] = now

        record_dict[_CREATED_BY] = user
        record_dict[_LAST_UPDATE_BY] = user

        # now save the items
        # logger.info(f"save dict: {str(record_dict)}")

        self.__table.put_item(Item=record_dict,
                              ConditionExpression=Attr(self.__PK).not_exists() & Attr(self.__SK).not_exists())

        return record_dict

    def add_raw_item(self, record: SingleTableRecord) -> Dict:
        self.__init()

        record_dict = record.as_dict()

        # set mandatory index keys
        self.__set_index_keys(record, record_dict)

        # now save the items
        self.__table.put_item(Item=record_dict,
                              ConditionExpression=Attr(self.__PK).not_exists() & Attr(self.__SK).not_exists())

        return record_dict

    def update_item(self, record: SingleTableRecord, user: str = None) -> Dict:
        self.__init()

        # set creation and last update time
        now = TimeUtils.get_time_iso8601()
        record_dict = record.as_dict()
        # logger.info(f"update_item called. record = {str(record_dict)}")

        # set mandatory index keys
        self.__set_index_keys(record, record_dict)

        # if not user:
        #     user = SessionContext.get_user_name()

        if _CREATION_TIME not in record_dict:
            raise ValueError(f"Missing attribute when updating record: '{_CREATION_TIME}'")

        record_dict[_LAST_UPDATE_TIME] = now
        record_dict[_LAST_UPDATE_BY] = user
        prev_version: int = record_dict[_VERSION]
        record_dict[_VERSION] = prev_version + 1

        # logger.info(f"updating record: {str(record_dict)}")

        # now save the items
        self.__table.put_item(Item=record_dict,
                              ConditionExpression=Attr(_VERSION).eq(prev_version))

        return record_dict

    def remove_item(self, pk: str, sk: str) -> None:
        self.__init()

        # todo: check ret val
        self.__table.delete_item(
            Key={
                self.__PK: pk,
                self.__SK: sk
            }
        )

    def remove_items(self, *, items: List[SingleTableRecord]) -> None:
        self.__init()

        with self.__table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={
                        'pk': item.produce_pk(),
                        'sk': item.produce_sk()
                    }
                )

    def batch_write_items(self, records: List[SingleTableRecord],
                          add_creation_time: bool = True,
                          update_last_update_time: bool = True) -> \
            List[Dict]:

        self.__init()

        dict_list: List[Dict] = list()
        now = TimeUtils.get_time_iso8601()
        with self.__table.batch_writer() as batch:
            for record in records:
                record_dict = record.as_dict()
                self.__set_index_keys(record, record_dict)
                if add_creation_time:
                    record_dict["creationTime"] = now
                if update_last_update_time:
                    record_dict["lastUpdateTime"] = now

                dict_list.append(record_dict)

            # now save the items
            for curr_record_dict in dict_list:
                batch.put_item(Item=curr_record_dict)

        return dict_list

    def __clean_single_table_indices_attributes(self, items: List[Dict]):
        for item in items:
            for att in [self.__PK, self.__SK, self.__GSI1_PK, self.__GSI1_SK]:
                if att in item:
                    del item[att]

    @staticmethod
    def _convert_to_low_level_dynamodb_dict(python_data: Dict) -> Dict:
        # this should be called by any mock that needs this.
        # Lazy-eval the dynamodb attribute (boto3 is dynamic!)
        # boto3.resource('dynamodb', region_name=self.region)
        # noinspection PyUnresolvedReferences
        serializer = boto3.dynamodb.types.TypeSerializer()
        low_level_copy = {k: serializer.serialize(v) for k, v in python_data.items()}
        return low_level_copy

    @staticmethod
    def _convert_to_high_level_dict(low_level_data: Dict) -> Dict:
        # this should be called by any mock that needs this.
        # Lazy-eval the dynamodb attribute (boto3 is dynamic!)
        # boto3.resource('dynamodb', region_name=self.region)

        # To go from low-level format to python
        # noinspection PyUnresolvedReferences
        deserializer = boto3.dynamodb.types.TypeDeserializer()
        python_data = {k: deserializer.deserialize(v) for k, v in low_level_data.items()}
        return python_data

    def __set_index_keys(self, record: SingleTableRecord, record_dict: Dict):
        record_dict[self.__PK] = record.produce_pk()
        record_dict[self.__SK] = record.produce_sk()
        gs1pk = record.produce_gsi1_pk()
        if gs1pk:
            record_dict[self.__GSI1_PK] = gs1pk
            gs1sk = record.produce_gsi1_sk()
            if gs1sk:
                record_dict[self.__GSI1_SK] = gs1sk

        # this is done in order not to null values in the index keys
        if self.__GSI1_PK in record_dict and not record_dict[self.__GSI1_PK]:
            del record_dict[self.__GSI1_PK]

        # this is done in order not to null values in the index keys
        if self.__GSI1_SK in record_dict and not record_dict[self.__GSI1_SK]:
            del record_dict[self.__GSI1_SK]

    def transact_write_items(self, table_name: str, high_level_items: List[Dict], add_last_update_time: bool = True) \
            -> List[Dict]:
        self.__init()

        """
        :param table_name:
        :param high_level_items:
        :param add_last_update_time:
        :return: response from dynamo_client.transact_write_items
        """
        dynamo_client = boto3.client("dynamodb")
        put_items_lists = []

        if add_last_update_time:
            now = TimeUtils.get_time_iso8601()
            for x in high_level_items:
                x["last_updated"] = now

        for x in high_level_items:
            low_level_item = self._convert_to_low_level_dynamodb_dict(x)
            put_items_lists.append({
                "Put": {
                    "Item": low_level_item,
                    "TableName": table_name
                }
            })

        return dynamo_client.transact_write_items(TransactItems=put_items_lists)


single_table_service: _SingleTableService = _SingleTableService()
