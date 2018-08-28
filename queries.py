get_actual_file_version_query = '''SELECT MAX(aci.fileVersion)
  FROM accredited_cert_info aci
WHERE aci.active = 1
AND aci.archive = 0
  ;'''

insert_cert_info_query = '''INSERT INTO accredited_cert_info
  SET
  fileVersion = %s,
  subjKeyId = %s,
  serial = %s,
  sha1Hash = %s,
  insertDateTime = %s,
  crlUrl = %s,
  location = %s
;'''

update_set_not_active_query = '''UPDATE accredited_cert_info aci
  SET aci.active = 0
  WHERE aci.active = 1
  AND aci.archive = 0
  ;'''

get_locations_query = '''SELECT destination
  FROM (
SELECT
  aci_1.location AS destination, aci_2.location
FROM accredited_cert_info aci_1
  LEFT JOIN accredited_cert_info aci_2
    ON aci_2.location = aci_1.location
    AND aci_2.insertDateTime >= SUBDATE(NOW(), INTERVAL %s MINUTE)
WHERE aci_1.active = 1
AND aci_1.insertDateTime < SUBDATE(NOW(), INTERVAL %s MINUTE)
AND aci_1.archive = 0
HAVING aci_2.location IS NULL
) AS tmp
;'''


delete_old_records_query = '''DELETE FROM accredited_cert_info
  WHERE insertDatetime < SUBDATE(NOW(), INTERVAL %s MINUTE)
  AND archive = 0
  AND active = 1
;'''