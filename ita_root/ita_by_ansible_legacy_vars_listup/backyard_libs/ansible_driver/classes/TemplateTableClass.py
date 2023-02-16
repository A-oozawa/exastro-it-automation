# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from flask import g
import json

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
from .TableBaseClass import TableBase


class TemplateTable(TableBase):
    """
    テンプレート管理のデータを取得し、定義変数を管理するクラス
    """

    TABLE_NAME = "T_ANSC_TEMPLATE_FILE"
    PKEY = "ANS_TEMPLATE_ID"

    def __init__(self, ws_db):
        """
        constructor
        """
        super().__init__(ws_db)
        self.table_name = TemplateTable.TABLE_NAME
        self.pkey = TemplateTable.PKEY

    def extract_variable(self):
        """
        変数を抽出する

        Returns:
            result_dict: { (tpl_var_name): set(var_name), ... }
        """
        g.applogger.debug(f"[Trace] Call {self.__class__.__name__} extract_variable()")

        result_dict = {}
        for row in self._stored_records.values():
            tpl_var_name = row['ANS_TEMPLATE_VARS_NAME']
            var_struct = json.loads(row['VAR_STRUCT_ANAL_JSON_STRING'])

            if tpl_var_name not in result_dict:
                result_dict[tpl_var_name] = set()

            for var_name, attr_flag in var_struct['Vars_list'].items():
                result_dict[tpl_var_name].add(var_name)

        return result_dict
