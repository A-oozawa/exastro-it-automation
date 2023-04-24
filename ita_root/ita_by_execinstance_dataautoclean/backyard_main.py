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
# class MainFunctions():
#   __init__(self):
#   InitFunction(self):
#   MainFunction(self):
#   EndFunction(self, result):
#   getOpeDelMenuList(self, OpeDelLists):
#   getTgtDelOpeList(self, TgtDelDate):
#   LogicalDeleteDB(self, DelList, TgtOpeList):
#   PhysicalDeleteDB(self, DelList, TgtOpeList):
#   getDataRelayStorageDir(self):
#   is_int(self, int_value):
#   DateCalc(self, AddDay):
# backyard_main(organization_id, workspace_id):
import os
import datetime
import shutil

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs


class MainFunctions():
    """
      �I�y���[�V�����폜�@���C�������N���X
    """
    def __init__(self):
        if getattr(g, 'USER_ID', None) is None:
            g.USER_ID = '110101'
        self.warning_flag = 0  # �x���t���O(1�F�x������)
        self.error_flag = 0    # �ُ�t���O(1�F�ُ픭��)
        self.test_mode = False
        self.ws_db = None
        self.operation_id_column_name = "OPERATION_ID"

    def InitFunction(self):
        """
          ��������
          Arguments:
            �Ȃ�
          Returns:
            �Ȃ�
        """
        # [����]�v���V�[�W���J�n
        FREE_LOG = g.appmsg.get_api_message("MSG-100001")
        g.applogger.debug(FREE_LOG)

        self.ws_db = DBConnectWs()

        # [����]DB�R�l�N�g����
        FREE_LOG = g.appmsg.get_api_message("MSG-100002")
        g.applogger.debug(FREE_LOG)

        # [����]�g�����U�N�V�����J�n
        FREE_LOG = g.appmsg.get_api_message("MSG-100004")
        self.ws_db.db_transaction_start()

    def MainFunction(self):
        """
          ���C������
          Arguments:
            �Ȃ�
          Returns:
            bool True:����@False:�ُ�
        """
        ret_bool = True
        OpeDelLists = []

        ret_bool, OpeDelLists = self.getOpeDelMenuList(OpeDelLists)

        for DelList in OpeDelLists:

            # [����] �e�[�u������ۊǊ����؂�f�[�^�̍폜�J�n(�e�[�u����:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100005", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)

            # �_���폜�����ɑΉ�����I�y���[�V�����̃��R�[�h��p�~
            TgtDelDate = DelList['LG_DATE'].strftime('%Y/%m/%d %H:%M:%S')
            TgtLogicalOpeList = self.getTgtDelOpeList(TgtDelDate)
            self.LogicalDeleteDB(DelList, TgtLogicalOpeList)
            # �����폜�����ɑΉ�����I�y���[�V�����̃��R�[�h���폜
            TgtDelDate = DelList['PH_DATE'].strftime('%Y/%m/%d %H:%M:%S')
            TgtPhysicsOpeList = self.getTgtDelOpeList(TgtDelDate)
            self.PhysicalDeleteDB(DelList, TgtPhysicsOpeList)
            # �폜����Ă���I�y���[�V�����ɕR�Â��Ă��郌�R�[�h���폜
            self.PhysicalDeleteDBbyOperationDelete(DelList)

            # [����] �e�[�u������ۊǊ����؂�f�[�^�̍폜����(�e�[�u����:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100006", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)
        return ret_bool

    def EndFunction(self, result):
        """
          �I������
          Arguments:
            �Ȃ�
          Returns:
            �Ȃ�
        """
        if result is True:
            # �R�~�b�g(���R�[�h���b�N������)
            FREE_LOG = g.appmsg.get_api_message("MSG-100016")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_commit()

            # �g�����U�N�V�����I��
            FREE_LOG = g.appmsg.get_api_message("MSG-100015")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_transaction_end(True)

            if self.warning_flag == 0:
                # [����]�v���V�[�W���I��(����)
                FREE_LOG = g.appmsg.get_api_message("MSG-100003")
                g.applogger.debug(FREE_LOG)

            else:
                # �v���V�[�W���I��(�x��)
                FREE_LOG = g.appmsg.get_api_message("MSG-100011")
                g.applogger.debug(FREE_LOG)

        else:
            # ���[���o�b�N(���R�[�h���b�N������)
            FREE_LOG = g.appmsg.get_api_message("MSG-100017")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_rollback()

            # �g�����U�N�V�����I��
            FREE_LOG = g.appmsg.get_api_message("MSG-100015")
            g.applogger.debug(FREE_LOG)

            self.ws_db.db_transaction_end(False)

            # �v���V�[�W���I��(�ُ�)
            FREE_LOG = g.appmsg.get_api_message("MSG-100010")
            g.applogger.debug(FREE_LOG)

    def getOpeDelMenuList(self, OpeDelLists):
        """
          �I�y���[�V�����폜�Ǘ��uT_COMN_DEL_OPERATION_LIST�v�̏��擾
          Arguments:
            OpeDelLists: �I�y���[�V�����폜�Ǘ��̎擾���
          Returns:
            bool(True,False), OpeDelLists
        """

        # �I�y���[�V�����폜�Ǘ����擾
        FREE_LOG = g.appmsg.get_api_message("MSG-100020")
        g.applogger.debug(FREE_LOG)

        OpeDelLists = []
        sql = "SELECT * FROM T_COMN_DEL_OPERATION_LIST WHERE DISUSE_FLAG='0'"
        DelLists = self.ws_db.sql_execute(sql)
        if len(DelLists) == 0:
            # �I�y���[�V�����폜�Ǘ��@���R�[�h���o�^
            return True, OpeDelLists

        for DelList in DelLists:

            tbl_info = {}

            # ���j���[�E�e�[�u���R�t���烁�j���[���擾
            sql = "SELECT * FROM T_COMN_MENU_TABLE_LINK WHERE MENU_ID = %s AND DISUSE_FLAG='0'"
            MenuTblLinkLists = self.ws_db.sql_execute(sql, [DelList["MENU_NAME"]])

            if len(MenuTblLinkLists) == 0:
                # ���j���[�E�e�[�u���R�t�Ƀ��j���[�����o�^�ł��B (���j���[:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100019", [DelList["MENU_NAME"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            MenuTblLinkList = MenuTblLinkLists[0]
            tbl_info['HISTORY_TABLE_FLAG'] = MenuTblLinkList['HISTORY_TABLE_FLAG']
            tbl_info['FILE_UPLOAD_COLUMNS'] = []
            if DelList['DATA_STORAGE_PATH']:
                tbl_info['FILE_UPLOAD_COLUMNS'].append(DelList['DATA_STORAGE_PATH'])
            RestNameConfig = {}
            # ���j���[�E�J�����R�t���烁�j���[���擾
            sql = "SELECT * FROM T_COMN_MENU_COLUMN_LINK WHERE MENU_ID = %s and DISUSE_FLAG = '0'"
            MenuColLinkLists = self.ws_db.sql_execute(sql, [DelList["MENU_NAME"]])

            if len(MenuColLinkLists) == 0:
                # ���j���[�E�J�����R�t�ɃJ������񂪖��o�^�ł��B(���j���[:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100018", [DelList["MENU_NAME"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            for MenuColLinkList in MenuColLinkLists:
                RestNameConfig[MenuColLinkList["COLUMN_NAME_REST"]] = MenuColLinkList["COL_NAME"]
                # �t�@�C���A�b�v���[�h�J��������
                if MenuColLinkList['COLUMN_CLASS'] in ('9', '20'):
                    # �t�@�C���A�b�v���[�h�z�u�ꏊ���ݒ肳��Ă���ꍇ�̔���
                    if MenuColLinkList['FILE_UPLOAD_PLACE']:
                        tbl_info['FILE_UPLOAD_COLUMNS'].append(MenuColLinkList['FILE_UPLOAD_PLACE'])
                    else:
                        tbl_info['FILE_UPLOAD_COLUMNS'].append("/uploadfiles/" + DelList["MENU_NAME"] + "/" + MenuColLinkList["COLUMN_NAME_REST"])

            # ��L�[���m�F
            if MenuTblLinkList['PK_COLUMN_NAME_REST'] not in RestNameConfig:
                # ���j���[�E�J�����R�t�ɃJ������񂪖��o�^�ł��B(���j���[:{})
                FREE_LOG = g.appmsg.get_api_message("MSG-100018", [DelList["MENU_NAME"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            # p1:�p�~�܂ł̓���
            tbl_info['LG_DAYS'] = DelList['LG_DAYS']
            # �p�~�܂ł̓����̑Ó����`�F�b�N
            if self.is_int(tbl_info['LG_DAYS']) is False:
                # �I�y���[�V�����폜�Ǘ��̍���[{}]�F�_���폜����[{}]���Ó��ł͂���܂���B
                FREE_LOG = g.appmsg.get_api_message("MSG-100012", [DelList["ROW_ID"], DelList["LG_DAYS"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            # p2:�����폜�܂ł̓���
            tbl_info['PH_DAYS'] = DelList['PH_DAYS']
            # �p�~�܂ł̓����̑Ó����`�F�b�N
            if self.is_int(tbl_info['PH_DAYS']) is False:
                # �I�y���[�V�����폜�Ǘ��̍���[{}]�F�����폜����[{}]���Ó��ł͂���܂���B
                FREE_LOG = g.appmsg.get_api_message("MSG-100013", [DelList["ROW_ID"], DelList["PH_DAYS"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            # �p�~�܂ł̓����ƕ����폜�܂ł̓����̑Ó����`�F�b�N
            if tbl_info['LG_DAYS'] >= tbl_info['PH_DAYS']:
                # �I�y���[�V�����폜�Ǘ��̍���[{}]�F�i�_���폜����[{}]���������폜����[{}]�j�ɂȂ��Ă��܂��B
                FREE_LOG = g.appmsg.get_api_message("MSG-100014", [DelList["ROW_ID"], DelList["LG_DAYS"], DelList["PH_DAYS"]])
                g.applogger.error(FREE_LOG)
                self.warning_flag = True
                continue

            # �ۑ����ԎZ�o
            tbl_info['LG_DATE'] = self.DateCalc(tbl_info['LG_DAYS'])

            tbl_info['PH_DATE'] = self.DateCalc(tbl_info['PH_DAYS'])

            # �����e�[�u����
            tbl_info['TABLE_NAME'] = MenuTblLinkList['TABLE_NAME']

            # �r���[��
            tbl_info['VIEW_NAME'] = MenuTblLinkList['VIEW_NAME']

            # �����e�[�u�����i�W���[�i���j
            tbl_info['TABLE_NAME_JNL'] = MenuTblLinkList['TABLE_NAME'] + "_JNL"

            # ��L�[��
            tbl_info['PKEY_NAME'] = RestNameConfig[MenuTblLinkList['PK_COLUMN_NAME_REST']]

            # �ŏI�X�V��ID
            tbl_info['LAST_UPD_USER_ID'] = 110101

            # �I�y���[�V�����폜�Ǘ���� (���:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100021", [str(tbl_info)])
            g.applogger.debug(FREE_LOG)

            OpeDelLists.append(tbl_info)

        return True, OpeDelLists

    def getTgtDelOpeList(self, TgtDelDate):
        """
          �폜�Ώۓ������Â����{�\����̃I�y���[�V�������擾
          Arguments:
            TgtDelDate:  �폜�Ώۓ���
          Returns:
            TgtOpeList: �폜�Ώۓ������Â����{�\����̃I�y���[�V����(uuid)
        """
        # �p�~����Ă��郌�R�[�h���Ώۂɂ���B
        sql = '''
              SELECT
                CONCAT('"', OPERATION_ID, '"') AS OPERATION_ID
              FROM
                T_COMN_OPERATION
              WHERE
                DATE_FORMAT(OPERATION_DATE, '%%Y/%%m/%%d %%H:%%i') <= %s
              '''
        rows = self.ws_db.sql_execute(sql, [TgtDelDate])
        TgtOpeList = ""
        for row in rows:
            if len(TgtOpeList) != 0:
                TgtOpeList += ","
            TgtOpeList += row['OPERATION_ID']
        return TgtOpeList

    def LogicalDeleteDB(self, DelList, TgtOpeList):
        """
          �폜�Ώۓ������Â����{�\����̃I�y���[�V�����̃��R�[�h��p�~
          Arguments:
            DelList: �폜�Ώۂ̃��j���[���
            TgtOpeList:  �폜�Ώۂ̃I�y���[�V����
          Returns:
            �Ȃ�
        """
        # �폜�Ώۂ̃I�y���[�V�������Ȃ��ꍇ
        if not TgtOpeList:
            return

        # �Ώۃ��j���[���r���[�̏ꍇ
        # �I�y���[�V����ID���Ȃ��e�[�u���̑Ή��uT_COMN_CONDUCTOR_NODE_INSTANCE�v
        # ����pView�̍쐬���K�v
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        # �Ώۃ��j���[���r���[�̏ꍇ�ASELECT�̓r���[���g�p
        sql = '''SELECT
                   {},
                   DISUSE_FLAG,
                   LAST_UPDATE_USER
                 FROM
                   {}
                 WHERE
                   DISUSE_FLAG = '0' AND
                   {} in ({})
              '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, TgtOpeList)

        rows = self.ws_db.sql_execute(sql)

        if len(rows) == 0:
            return

        # [����] �e�[�u������ۊǊ����؂ꃌ�R�[�h�̔p�~(�e�[�u����:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100007", [DelList["TABLE_NAME"]])
        g.applogger.debug(FREE_LOG)

        for row in rows:
            # �_���폜�Ώۂ̃��R�[�h��p�~����B
            row['LAST_UPDATE_USER'] = DelList['LAST_UPD_USER_ID']
            row['DISUSE_FLAG'] = '1'
            history_table = False
            if DelList['HISTORY_TABLE_FLAG'] == '1':
                history_table = True

            self.ws_db.table_update(DelList['TABLE_NAME'], row, DelList['PKEY_NAME'], history_table)

    def PhysicalDeleteDB(self, DelList, TgtOpeList):
        """
          �폜�Ώۓ������Â����{�\����̃I�y���[�V�����̃��R�[�h���폜
          Arguments:
            DelList: �폜�Ώۂ̃��j���[���
            TgtOpeList:  �폜�Ώۂ̃I�y���[�V����
          Returns:
            �Ȃ�
        """
        # �폜�Ώۂ̃I�y���[�V�������Ȃ��ꍇ
        if not TgtOpeList:
            return

        # �Ώۃ��j���[���r���[�̏ꍇ
        # �I�y���[�V����ID���Ȃ��e�[�u���̑Ή��uT_COMN_CONDUCTOR_NODE_INSTANCE�v
        # ����pView�̍쐬���K�v
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        # �Ώۃ��j���[���r���[�̏ꍇ�ASELECT�̓r���[���g�p
        sql = '''SELECT
                   {}
                 FROM
                   {}
                 WHERE
                   {} in ({})
              '''.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name, TgtOpeList)

        rows = self.ws_db.sql_execute(sql)

        PkeyList = []
        PkeyString = ""
        # �����Ώۂ̃��R�[�h��Pkey���擾
        for row in rows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

        # �폜�Ώۂ̃��R�[�h���Ȃ��ꍇ
        if len(PkeyList) == 0:
            return

        # �����Ώۂ̃��R�[�h�ɕR�Â��Ă���t�@�C���A�b�v���[�h�J�����̃t�@�C�����폜
        for Pkey in PkeyList:
            for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                if os.path.isdir(DelPath):
                    # [����] �e�[�u���ɕR�Â��s�v�f�B���N�g���폜(�e�[�u����:({}) �f�B���N�g����:({}))
                    FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                    g.applogger.debug(FREE_LOG)
                    shutil.rmtree(DelPath)

        # [����] �e�[�u������ۊǊ����؂ꃌ�R�[�h�̕����폜(�e�[�u����:{})
        FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME"]])
        g.applogger.debug(FREE_LOG)

        sql = '''DELETE
                 FROM
                   {}
                 WHERE
                   {} in ({})
              '''.format(DelList['TABLE_NAME'], DelList['PKEY_NAME'], PkeyString)

        rows = self.ws_db.sql_execute(sql)

        if DelList['HISTORY_TABLE_FLAG'] == '1':
            sql = '''DELETE
                     FROM
                       {}
                     WHERE
                       {} in ({})
                  '''.format(DelList['TABLE_NAME_JNL'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            # [����] �e�[�u������ۊǊ����؂ꃌ�R�[�h�̕����폜(�e�[�u����:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100008", [DelList["TABLE_NAME_JNL"]])
            g.applogger.debug(FREE_LOG)

    def PhysicalDeleteDBbyOperationDelete(self, DelList):
        """
          �폜����Ă���I�y���[�V�����ɕR�Â��Ă���I�y���[�V�����̃��R�[�h���폜
          Arguments:
            DelList: �폜�Ώۂ̃��j���[���
          Returns:
            �Ȃ�
        """
        MasterRows, JournalRows = self.getOperationDeleteRows(DelList)

        PkeyList = []
        PkeyString = ""
        # �����Ώۂ̃��R�[�h��Pkey���擾
        for row in MasterRows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

        # �폜�Ώۂ̃��R�[�h������ꍇ
        if len(PkeyList) != 0:
            # �����Ώۂ̃��R�[�h�ɕR�Â��Ă���t�@�C���A�b�v���[�h�J�����̃t�@�C�����폜
            for Pkey in PkeyList:
                for TgtPath in DelList['FILE_UPLOAD_COLUMNS']:
                    DelPath = "{}/{}/{}".format(self.getDataRelayStorageDir(), TgtPath, Pkey)
                    if os.path.isdir(DelPath):
                        # [����] �e�[�u���ɕR�Â��s�v�f�B���N�g���폜(�e�[�u����:({}) �f�B���N�g����:({}))
                        FREE_LOG = g.appmsg.get_api_message("MSG-100009", [DelList["TABLE_NAME"], DelPath])
                        g.applogger.debug(FREE_LOG)
                        shutil.rmtree(DelPath)

            sql = '''DELETE
                    FROM
                    {}
                    WHERE
                    {} in ({})
                '''.format(DelList['TABLE_NAME'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            #	[����] �폜���ꂽ�I�y���[�V�����ɕR�Â��Ă��郌�R�[�h�̕����폜(�e�[�u����:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME"]])
            g.applogger.debug(FREE_LOG)

        PkeyList = []
        PkeyString = ""
        # �����Ώۂ̗������R�[�h��Pkey���擾
        for row in JournalRows:
            PkeyList.append(row[DelList['PKEY_NAME']])
            if len(PkeyString) != 0:
                PkeyString += ","
            PkeyString += "'" + row[DelList['PKEY_NAME']] + "'"

            sql = '''DELETE
                     FROM
                       {}
                     WHERE
                       {} in ({})
                  '''.format(DelList['TABLE_NAME_JNL'], DelList['PKEY_NAME'], PkeyString)

            rows = self.ws_db.sql_execute(sql)

            #	[����] �폜���ꂽ�I�y���[�V�����ɕR�Â��Ă��郌�R�[�h�̕����폜(�e�[�u����:{})
            FREE_LOG = g.appmsg.get_api_message("MSG-100022", [DelList["TABLE_NAME_JNL"]])
            g.applogger.debug(FREE_LOG)

    def getOperationDeleteRows(self, DelList):
        # �Ώۃ��j���[���r���[�̏ꍇ
        # �I�y���[�V����ID���Ȃ��e�[�u���̑Ή��uT_COMN_CONDUCTOR_NODE_INSTANCE�v
        # ����pView�̍쐬���K�v
        SelectObjName = DelList['TABLE_NAME']
        if DelList['VIEW_NAME']:
            SelectObjName = DelList['VIEW_NAME']

        MasterRows = []
        JournalRows = []
        # Terraform��ƊǗ��n�e�[�u���ɂ��āARUN_MODE:3(���\�[�X�폜)�̏ꍇ�I�y���[�V����ID���w�肳��Ȃ��̂ŁA�폜�ΏۂƂ��ď��O����B
        Terrafomesql = '''
                    select {} from {} TAB_A
                    where NOT EXISTS
                        (select
                            *
                        from
                            (select * from T_COMN_OPERATION) TAB_B
                        where
                            TAB_A.{} = TAB_B.OPERATION_ID
                        ) AND NOT TAB_A.RUN_MODE = '4'
                    '''

        Otherssql = '''
                    select {} from {} TAB_A
                    where NOT EXISTS
                        (select
                            *
                        from
                            (select * from T_COMN_OPERATION) TAB_B
                        where
                            TAB_A.{} = TAB_B.OPERATION_ID
                        )
                    '''

        OpeDelJnlPkeyLists = {}
        # �Ώۃ��j���[���r���[�̏ꍇ�ASELECT�̓r���[���g�p
        if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST","T_TERC_EXEC_STS_INST"):
            sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)
        else:
            sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName, self.operation_id_column_name)

        MasterRows = self.ws_db.sql_execute(sql)

        if DelList['HISTORY_TABLE_FLAG'] == '1':
            if DelList['TABLE_NAME'] in ("T_TERE_EXEC_STS_INST","T_TERC_EXEC_STS_INST"):
                sql = Terrafomesql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)
            else:
                sql = Otherssql.format(DelList['PKEY_NAME'], SelectObjName + "_JNL", self.operation_id_column_name)

            JournalRows = self.ws_db.sql_execute(sql)

        return MasterRows, JournalRows

    def getDataRelayStorageDir(self):
        """
          �f�[�^�����C�X�g���[�W�̃p�X�擾
        Arguments:
          �Ȃ�
        Returns:
          �f�[�^�����C�X�g���[�W�̃p�X
        """
        return os.environ.get('STORAGEPATH') + "{}/{}".format(g.get('ORGANIZATION_ID'), g.get('WORKSPACE_ID'))

    def is_int(self, int_value):
        """
          ���l����
        Arguments:
          int_value: ���l
        Returns:
          bool True:���l False:���l�ȊO
        """
        if not int_value:
            return False
        try:
            if not isinstance(int_value, int):
                int(int_value, 10)
        except ValueError:
            return False
        if int_value <= 0:
            return False

    def DateCalc(self, AddDay):
        """
          ���ݎ����ɓ������Z
        Arguments:
          AddDay: ���Z����
        Returns:
          ���ݎ����ɓ������Z��������
        """
        NowDate = datetime.datetime.now()
        AddDate = datetime.timedelta(days=AddDay)
        return NowDate - AddDate


def backyard_main(organization_id, workspace_id):
    """
      �o�b�N���[�h���C������
    Arguments:
      organization_id: organization id
      workspace_id: workspace id
    Returns:
      �Ȃ�
    """
    g.applogger.debug("ita_by_execinstance_dataautoclean backyard_main started")

    obj = MainFunctions()

    obj.InitFunction()

    ret = obj.MainFunction()

    obj.EndFunction(ret)
