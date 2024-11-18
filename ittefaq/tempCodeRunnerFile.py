:
  #   request_id = int(url.split("/")[-1])
  #   print(f"trying: {retries}")
  #   if response:
  #     status_report = {
  #       "id": request_id,
  #       "status_code": response.status_code
  #     }
  #     insert_status(connection, status_report)
    
  #   if not response:
  #     return