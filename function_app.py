import azure.functions as func
import json
import logging
from datetime import datetime
import os
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="submit_feedback")
@app.route(route="submit_feedback", methods=["POST"])
def submit_feedback(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Feedback function triggered.")

    try:
        # Parse request
        feedback_data = req.get_json()
        name = feedback_data.get("name")
        email = feedback_data.get("email")
        message = feedback_data.get("message")

        if not all([name, email, message]):
            return func.HttpResponse(
                json.dumps({"error": "Missing one or more fields"}),
                status_code=400,
                mimetype="application/json"
            )

        # ✅ Get connection string from environment
        connection_string = os.environ["AzureStorageConnectionString"]

        # ✅ Connect to Table Storage
        table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
        table_client = table_service.get_table_client(table_name="FeedbackTable")

        # ✅ Create entity (record)
        record = {
            "PartitionKey": "Feedback",
            "RowKey": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),  # unique ID
            "name": name,
            "email": email,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        # ✅ Insert into Azure Table
        table_client.create_entity(entity=record)

        logging.info(f"Feedback saved: {record}")

        return func.HttpResponse(
            json.dumps({"success": True, "data": record}),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON format"}),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error saving feedback: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
