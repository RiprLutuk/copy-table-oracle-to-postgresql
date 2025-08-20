import sys
import psycopg2 # pyright: ignore[reportMissingModuleSource]
import oracledb as cx_Oracle # type: ignore
import tempfile
import csv
import time
import logging
from .config import ORACLE_USER, ORACLE_PASS, ORACLE_SCHEMA, PG_CONN, ORACLE_HOST, ORACLE_PORT, ORACLE_SID

# --- Oracle Connection Setup ---
cx_Oracle.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_9")
# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sync.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_TABLES = [
"brim_zf_ont_all_history",
# "brim_zm_exec_log",
# "housemaster_monthly",
# "custmaster_monthly",
# "brim_zn_nagratrig_1_hist",
# "a_hp_servco_sallocation_arc",
# "zyx_histchangefield02",
# "brim_zf_ont_offline_hist",
# "brim_prov_all_hist1",
# "brim_box_status_batch_det_hist",
# "brim_zf_result",
# "histaddress",
# "brim_zm_protrig_cm_hist",
# "brim_prov_all",
# "zprog_error_log",
# "boxinvtry",
# "brim_zm_result",
# "brim_zf_alarm_events_zte",
# "modemregdereghistory",
# "brim_zn_protrig_ott",
# "brim_zf_protrig_ont_hist",
# "brim_box_info",
# "brim_v_box_pairing_rec",
# "a_hp_report_g2a_batch_detail",
# "brim_boxinvtry_update_hist",
# "brim_zf_alarm_events_huawei",
# "brim_scc_pair_batch_detail",
# "zyx_histchangefield01",
# "address",
# "housemaster",
# "house_service_group",
# "a_hp_servco_site_allocation",
# "addl_boxinvtry",
# "brim_box_sap_daily_gi",
# "a_hp_house_info",
# "a_hp_hist_bulk_edit",
# "a_hp_servco_sallocation_hist",
# "brim_box_sap_mov_detail",
# "a_hp_serviceable_apr2024",
# "brim_prov_wo",
# "a_hp_segre_ln_xl",
# "brim_custmaster",
# "a_hp_memo_active",
# "brim_zn_fmx_product",
# "a_hp_fibernode_ori",
# "a_hp_amdocs_xl_done",
# "a_hp_servco_xl_amdocs",
# "a_hp_hist_housemaster",
# "a_hp_hist_memo_active",
# "brim_zn_nagratrig_2",
# "brim_zf_network_gpon_addr_temp",
# "brim_prog_error_log",
# "brim_prov_all_hist2",
# "a_hp_servco_site_disable",
# "brim_prov_all_log",
# "a_hp_m_bentley_ampli",
# "log_exception_api_dte",
# "brim_zn_rec_product_hist",
# "a_hp_batch_edit_detail",
# "brim_zm_rec_boxinvtry",
# "brim_zn_rec_pairing",
# "brim_send_refresh_log",
# "brim_housemaster_update_hist",
# "brim_zh_protrig_ottpartner",
# "brim_box_sap_mov_detail_hist",
# "brim_scc_pair_log_update",
# "commentmaster_custnull",
# "a_hp_batch_detail",
# "brim_box_status_batch_detail",
# "v_box_pairing_temp",
# "brim_box_batch_detail_hist",
# "a_temp_update_postalcode_hist",
# "brim_zf_alarm_events_zte_af",
# "brim_zw_wvtrig_1",
# "brim_scc_unpair_batch_detail",
# "brim_prov_wo_hist",
# "brim_scc_pair_log_hist",
# "brim_zn_ott_product",
# "brim_voucher_hist",
# "commentmaster",
# "brim_voucher",
# "brim_box_sap_pairing_ftax",
# "a_hp_site_account_log",
# "brim_box_location_batch_detail",
# "brim_zn_product",
# "a_hp_servco_contract_batch_d",
# "a_hp_network_batch_detail",
# "a_hp_network_migration",
# "a_hp_servco_rfs_batch_det",
# "brim_zm_bcc_subs_airflow",
# "brim_voucher_detail",
# "brim_zn_rec_product",
# "a_hp_hist_rfs_date",
# "brim_zm_mac_all_test",
# "brim_zf_ont_status_zte",
# "a_hp_memo_rebuild",
# "brim_zm_mac_all_bulk",
# "brim_box_status_daily_amdocs",
# "brim_zf_ont_avail_bck",
# "brim_zm_group_block_ip",
# "a_hp_batch_update_house_info",
# "brim_zm_bcc_error_log",
# "brim_zm_prov_doe_hist",
# "brim_zm_protrig_cm",
# "brim_zm_rec_bcc_subs_airflow",
# "a_hp_pole_history",
# "brim_zf_ont_rg_boxinvtry",
# "brim_zf_list_nms",
# "brim_scc_unpair_log_hist",
# "boxtechlist",
# "a_hp_servco_reb_rfs_batch_det",
# "a_hp_node_split_swap_detail",
# "brim_vzf_network_gpon_city",
# "brim_zf_network_device_grp",
# "brim_zf_ont_check_bulk_hist",
# "brim_zf_rec_ont_all",
# "brim_zf_ont_all",
# "a_hp_m_pole",
# "alarmeventstemp",
# "brim_box_wv_batch_detail",
# "brim_zf_network_gpon_addr",
# "brim_zm_mac_all",
# "brim_zm_mac_all_prov",
# "a_hp_asg_sallocation_batch_d",
# "brim_zf_avs_xl",
# "brim_zm_bcc_subs",
# "brim_zm_rec_bcc_subs",
# "brim_zn_nagratrig_1",
# "brim_zn_suspend_scc",
# "brim_zf_list_aaa",
# "brim_zf_network_batch_detail",
# "brim_box_wv_register",
# "brim_zf_aaa_counting",
# "brim_zf_alarm_events_huawei_af",
# "brim_box_batch_detail",
# "brim_box_batch_det_dbl",
# "brim_box_tc_counter",
# "a_hp_hist_rebuild_rfs_date",
# "a_hp_batch",
# "brim_zf_ont_all_avail",
# "brim_scc_pair_batch",
# "brim_zf_fail",
# "brim_zf_ont_status_huawei",
# "brim_zm_online_ptd_email",
# "brim_zf_ont_check_bulk",
# "brim_zw_rec_status",
# "a_hp_oa_batch_detail_siteid",
# "brim_vzf_network_gpon_avail",
# "brim_vzf_network_gpon_backup",
# "brim_zf_protrig_ont_temp",
# "brim_zs_protrig_rg_hist",
# "a_hp_batch_edit_detail_double",
# "brim_zf_protrig_splitter",
# "a_hp_infra_ownership",
# "brim_zf_ont_avail",
# "brim_box_sap_reset_status_hist",
# "brim_zw_wvtrig_2",
# "brim_box_status_batch_hist",
# "brim_zf_ont_autofind",
# "a_hp_nn_report",
# "brim_zf_network_dev_grp_hist",
# "sub_district_new",
# "a_hp_m_postal_code",
# "brim_zf_exec_log_crm",
# "a_temp_update_postalcode",
# "a_hp_pole_migration",
# "a_hp_house_info_abd",
# "a_hp_report_temp_linknet",
# "brim_zs_result",
# "brim_zf_protrig_ont",
# "brim_zf_ont_offline",
# "a_hp_hist_memo_rebuild",
# "brim_box_lelang",
# "brim_box_mfg_batch_detail",
# "brim_zw_product",
# "brim_zf_splitter",
# "brim_box_wv_free_batch_detail",
# "brim_box_sap_mov",
# "brim_zf_ont_pppoe",
# "a_hp_m_dist_ref",
# "brim_zw_rec_product",
# "a_hp_wttx_info",
# "brim_zf_ont_nms_all",
# "brim_zf_avs_ont_check",
# "brim_box_mac_vendor",
# "a_hp_memo_active_no",
# "brim_zf_avs_offline",
# "brim_box_batch_det_dbl_xl",
# "brim_zn_rec_product_selisih",
# "a_hp_m_fibernode",
# "a_hp_mgt_fibernode_temp",
# "brim_zf_ont_history",
# "a_hp_fibernode_first_active",
# "a_hp_batch_json_detail",
# "a_hp_fibernode_age",
# "brim_zm_rec_bcc_del",
# "a_hp_m_fibernode_check_apt",
# "a_hp_report_g2a_sales",
# "brim_zf_ont_nms",
# "schedareas",
# "a_hp_m_postal_code_history",
# "brim_zf_ont_selisih",
# "brim_box_sap_mov_hist",
# "brim_scc_unpair_batch",
# "brim_zf_fdt",
# "a_hp_fibernode_ds",
# "tb_user_right",
# "a_hp_servco_contract_batch",
# "a_hp_infra_ownership_network",
# "brim_zf_network_batch",
# "techs",
# "brim_prov_others",
# "acctareadesig",
# "a_hp_servco_site_report",
# "brim_box_status_fix_history",
# "brim_zm_fiber_cmts_grp",
# "a_hp_m_sales_code",
# "brim_zf_ont_ipoe",
# "brim_zm_protrig_cm_lisa",
# "a_hp_network_hist",
# "a_hp_node_split_swap",
# "a_hp_request_dwi",
# "brim_box_status_batch",
# "tbl_log",
# "a_hp_memo_rebuil_hist",
# "brim_zf_ont_autofind_hist",
# "a_hp_io_notes",
# "a_hp_temp_update_clust",
# "a_hp_temp_update_block",
# "brim_zf_ont_status_avs",
# "brim_zm_online_ptd_file",
# "tb_user_ads",
# "a_hp_batch_detail_double",
# "a_hp_servco_rfs_batch_d",
# "a_hp_m_fibernode_hist",
# "brim_zf_double_aaa",
# "a_hp_batch_edit",
# "brim_zm_online_ptd",
# "tb_user",
# "a_hp_network_batch",
# "a_hp_asg_sallocation_cluster",
# "brim_zn_package_channel",
# "boxinvtry_site_double",
# "brim_zs_rec_rg_all",
# "brim_voice_pair_batch_detail",
# "brim_zf_device",
# "a_hp_memo_rebuild_no",
# "brim_zf_device_nni",
# "brim_zs_rg_all",
# "brim_zm_online_ptd_batch",
# "brim_zf_ont_status_avs_bck",
# "brim_box_sap_daily_gi_log",
# "brim_zf_network_batch_det_dbl",
# "brim_box_wv_free_batch",
# "v_voice_pairing_temp",
# "brim_box_location_batch",
# "hpdb_download_log",
# "a_hp_update_demo2",
# "brim_zw_rec_product_selisih",
# "brim_zm_modem_exclude_hist",
# "brim_box_refurbish_batch_det",
# "a_hp_servco_reb_rfs_batch_d",
# "a_hp_servco_rfs_rebuild",
# "brim_master_product",
# "a_hp_batch_detail_del",
# "brim_migration_log",
# "brim_box_mfg_batch",
# "brim_voucher_stb_exp",
# "code36",
# "a_hp_oa_batch_detail_servco",
# "send_refresh_error",
# "alarm_events_huawei_test",
# "a_hp_oa_batch_detail",
# "code95",
# "brim_box_sap_histchange",
# "a_hp_update_demo1",
# "a_hp_network_batch_detail_fail",
# "a_hp_servco_rfs_rebuild_bat_d",
# "a_hp_servco_rfs_batch_d_fail",
# "brim_box_batch_hist",
# "brim_zf_uplink_router",
# "complexmaster",
# "brim_box_sap_voice_pair_ftax",
# "brim_box_voice_batch_detail",
# "brim_box_voice",
# "a_hp_update_data",
# "a_hp_m_city_mobile",
# "a_hp_verdi_dummy",
# "a_hp_verdi_nro",
# "tb_user_menu",
# "brim_zm_cust_test",
# "brim_zs_protrig_rg",
# "brim_zn_ott_pid_ratecode",
# "brim_zf_group_ratecode",
# "brim_zm_group_ratecode",
# "brim_zf_hub",
# "brim_zf_bras_fail",
# "brim_zn_package_ratecode",
# "a_hp_network_migration_bck",
# "box_hist_temp",
# "brim_zn_channel",
# "brim_zs_group_ratecode",
# "tb_user_ads_disable",
# "brim_zf_vlanid_detail",
# "a_hp_report_g2a_batch",
# "a_hp_asg_siteallocation_batch",
# "brim_box_batch",
# "brim_zf_result_olt",
# "brim_box_mfg",
# "brim_box_upload_error_log",
# "a_hp_servco_contract_batch_d_d",
# "brim_box_bequip_mfg",
# "brim_zm_cmts_group_nat",
# "brim_voice_pair_batch",
# "brim_product_bank",
# "brim_zm_speed_upg_mapping",
# "brim_zf_protrig_olt",
# "a_hp_segre_fibernode_non_xl",
# "brim_zn_package",
# "box_hist_check",
# "brim_zf_fdt_hist",
# "brim_box_user",
# "brim_zm_modem_exclude",
# "brim_box_voice_batch_det_dbl",
# "brim_box_voice_msh_production",
# "brim_zm_cmts",
# "brim_zw_rec_file",
# "brim_zm_group_speed",
# "brim_box_status_movement",
# "brim_zn_nagra_error_code_ext",
# "brim_zn_ott_pid",
# "brim_seq",
# "boxinvtry_testxl",
# "brim_zf_nni_router",
# "brim_zn_rec_file",
# "brim_zs_bras_fail",
# "a_hp_city_ds",
# "brim_box_stb_mac_update_hist",
# "brim_zm_cmts_pe",
# "brim_box_wv_batch",
# "tb_app_name",
# "brim_zf_ont_exclude",
# "brim_zf_fdt_area",
# "brim_zn_nagra_error_code",
# "a_hp_m_city_group",
# "brim_zf_network_batch_dbl_exl",
# "a_hp_m_branch",
# "a_hp_m_ftax",
# "a_hp_error_log",
# "a_hp_m_area",
# "brim_box_bequip",
# "brim_zn_cmd_log",
# "brim_box_status_access_group",
# "brim_zf_nni",
# "a_hp_servco_rfs_batch",
# "brim_zf_group_speed",
# "brim_zm_group_speed_hist",
# "brim_zs_group_speed",
# "brim_voice_pair_log_hist",
# "brim_zm_hub",
# "a_hp_m_histtype",
# "brim_zf_ont_check",
# "brim_trig_error_log",
# "brim_zn_package_ratecode_hist",
# "a_hp_partnership_site",
# "a_hp_servco_contract",
# "brim_zf_avs_ctype",
# "brim_zw_cmd",
# "brim_zn_rec_file_progress",
# "tb_app_group",
# "a_hp_partnership_name",
# "brim_box_location",
# "a_hp_servco",
# "brim_zh_sku_ratecode",
# "a_hp_memo_active_type",
# "brim_box_trans_type",
# "brim_zn_cmd",
# "brim_box_voice_batch",
# "brim_zf_down_cause",
# "brim_zf_m_down_cause",
# "brim_zf_nms_params",
# "brim_zf_vlanid",
# "brim_zn_channel_genre",
# "brim_box_bxstatus",
# "brim_box_sap_iplant",
# "brim_zf_group1",
# "brim_zm_group1",
# "brim_zn_source_id",
# "brim_zf_device_series",
# "brim_zn_progid_desc",
# "brim_box_vendor",
# "brim_zf_cmd",
# "brim_zm_isp",
# "a_hp_m_custstatus",
# "a_hp_m_histstat",
# "a_hp_m_site_ordnum_plant",
# "a_hp_servco_rebuild_rfs_batch",
# "brim_zf_olt_bulk_upload",
# "brim_zm_cmts_cluster",
# "brim_box_sap_exclude_status",
# "brim_zf_domain",
# "brim_zm_rec_file",
# "brim_zs_cmd",
# "brim_zw_rec_file_progress",
# "a_hp_asg_sallocation_batch_f",
# "a_hp_partnership_schema",
# "brim_box_place",
# "brim_zf_device_site_type",
# "a_hp_mview",
# "a_hp_m_housetype",
# "a_hp_m_pole_vendor",
# "a_hp_m_site_classifications",
# "brim_zn_rec_step",
# "brim_zw_rec_step",
# "a_hp_m_fibernode_capacity",
# "brim_box_sap_mov_type",
# "brim_box_user_group",
# "brim_voice_unpair_batch",
# "brim_zf_device_odn_type",
# "brim_zf_nms",
# "brim_zf_vendor",
# "a_hp_m_infra_ownership",
# "brim_box_vendor_list",
# "brim_zf_uplink_type",
# "a_hp_m_housestatus",
# "a_hp_oa_batch",
# "a_hp_summary_hp",
# "brim_voice_unpair_batch_detail",
# "brim_zf_brand",
# "brim_zf_construct_ratio",
# "brim_zf_network_port_type",
# "brim_zf_ont_reboot",
# "synch_time_ddl",
# "a_hp_memo_rebuild_type",
# "brim_zn_group1",
# "a_hp_batch_del",
# "a_hp_memo_type",
# "a_hp_m_deployment_type",
# "a_hp_m_fgroup",
# "a_hp_m_ftype",
# "a_hp_m_wttx",
# "a_hp_rebuild_status",
# "brim_box_refurbish_batch",
# "brim_zf_bras",
# "brim_zm_bcc_cluster",
# "brim_zm_cmd",
# "brim_box_sap_reset_status",
# "brim_voice_unpair_log_hist",
# "brim_zf_cust_network_traffic",
# "brim_zm_exclude_cmts_cluster",
# "brim_zn_pairing_nagra",
# "brim_zn_rec_date",
# "a_hp_batch_detail_fail",
# "a_hp_batch_edit_detail_fail",
# "a_hp_servco_reb_rfs_batch_d_d",
# "a_hp_servco_reb_rfs_batch_d_f",
# "a_hp_servco_rfs_batch_d_double",
# "a_hp_site_alloc_log",
# "a_hp_update_data_hist",
# "brim_box_status_error_log",
# "brim_box_voice_batch_dbl_xl",
# "brim_bvc_payment_code",
# "brim_prov_all_hist",
# "brim_zf_aaa_diff",
# "brim_zf_avs",
# "brim_zf_list_service_port",
# "brim_zm_bcc_dhcp_cmts",
# "brim_zm_bcc_dhcp_product",
# "brim_zm_bcc_fail",
# "brim_zm_rec_cmts",
# "brim_zm_rec_product",
# "brim_zm_result_bcc",
# "brim_zn_product_nagra",
# "brim_zn_product_nagra_copy",
# "brim_zn_rec_product_diff_all",
# "brim_zn_rec_product_diff_hist",
# "brim_zr_protrig_router",
# "brim_zyx_histchangefield02",
# "buy_addon_blacklist",
# "buy_addon_blacklist_trial",
# "confirm_cust_info",
# "confirm_log",
# "confirm_log_token",
# "firstcloud_ratecode",
# "a_hp_servco_contract_batch_d_f",
# "box_sap_pairing_ftax",
# "box_sap_voice_pairing_ftax",
# "brim_check_acc_network",
# "brim_zf_aaa_min_brim",
# "brim_zf_brim_min_aaa",
# "brim_zf_brim_min_nms",
# "brim_zf_device_info",
# "brim_zf_network_error_log",
# "brim_zf_nms_min_brim",
# "brim_zf_olt_config_hist",
# "brim_zf_ont_dashboard",
# "brim_zm_cmd_log",
# "brim_zm_cmd_log_bcc",
# "brim_zm_online_ptd_hist",
# "brim_zn_rec_pairing_cm",
# "brim_zn_rec_product_cm",
# "brim_zn_rec_product_diff",
# "brim_zn_rec_product_diff_cm",
# "brim_zn_rec_status_diff",
# "brim_zw_rec_product_cm",
# "brim_zw_rec_product_diff_cm",
# "zyx_histchangefield03",
# "zyx_histchangefield04"
]

def sync_table(table_name, ora_cur, pg_cur, pg_conn):
    start_time = time.time()

    # ambil kolom target PostgreSQL
    pg_cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table_name,))
    pg_columns = [r[0] for r in pg_cur.fetchall()]

    if not pg_columns:
        logger.warning(f"Table {table_name} tidak ditemukan di PostgreSQL, skip...")
        return

    # truncate target table
    pg_cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
    pg_conn.commit()
    logger.info(f"🧹 {table_name}: truncated sebelum insert.")

    # cek jumlah row di Oracle
    ora_cur.execute(f"SELECT COUNT(*) FROM {ORACLE_SCHEMA}.{table_name.upper()}")
    total_count = ora_cur.fetchone()[0]
    logger.info(f"📊 {table_name}: total {total_count} rows di Oracle.")

    # query ambil data
    ora_cur.execute(f"SELECT {', '.join([c.upper() for c in pg_columns])} FROM {ORACLE_SCHEMA}.{table_name.upper()}")

    # fetch mode
    if total_count < 500_000:
        # fetch sekaligus
        rows = ora_cur.fetchall()
        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmpfile:
            writer = csv.writer(tmpfile, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in rows:
                clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
                writer.writerow(clean_row)
            tmpfile.flush()
            tmpfile.seek(0)
            pg_cur.copy_expert(
                f"""
                COPY {table_name} ({', '.join(pg_columns)})
                FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                """,
                tmpfile
            )
        pg_conn.commit()
        logger.info(f"🎉 {table_name}: sync selesai, inserted {len(rows)} rows.")
    else:
        # fetch per batch
        batch_size = 500_000
        total_rows = 0
        chunk = 0
        while True:
            rows = ora_cur.fetchmany(batch_size)
            if not rows:
                break
            chunk += 1
            with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=False) as tmpfile:
                writer = csv.writer(tmpfile, delimiter="^", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in rows:
                    clean_row = ["" if v is None else str(v).replace("\x00", "") for v in row]
                    writer.writerow(clean_row)
                tmpfile.flush()
                tmpfile.seek(0)
                pg_cur.copy_expert(
                    f"""
                    COPY {table_name} ({', '.join(pg_columns)})
                    FROM STDIN WITH (FORMAT CSV, DELIMITER '^', QUOTE '"', NULL '')
                    """,
                    tmpfile
                )
            pg_conn.commit()
            total_rows += len(rows)
            logger.info(f"✅ {table_name}: chunk {chunk}, total {total_rows} rows inserted...")

        logger.info(f"🎉 {table_name}: sync selesai, inserted {total_rows} rows.")

    elapsed = time.time() - start_time
    logger.info(f"⏱️  {table_name}: selesai dalam {elapsed:.2f} detik.\n")


def main():
    if len(sys.argv) > 1:
        tables = [t.lower() for t in sys.argv[1:]]
    else:
        tables = DEFAULT_TABLES

    # --- Oracle connect via SID ---
    dsn = cx_Oracle.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
    ora_conn = cx_Oracle.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=dsn)
    ora_cur = ora_conn.cursor()

    # --- PostgreSQL connect ---
    pg_conn = psycopg2.connect(**PG_CONN)
    pg_cur = pg_conn.cursor()

    for tbl in tables:
        try:
            sync_table(tbl, ora_cur, pg_cur, pg_conn)
        except Exception as e:
            logger.error(f"❌ Error sync {tbl}: {e}", exc_info=True)

    pg_cur.close()
    pg_conn.close()
    ora_cur.close()
    ora_conn.close()


if __name__ == "__main__":
    main()
