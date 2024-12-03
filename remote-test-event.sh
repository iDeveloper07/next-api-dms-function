#! /bin/bash
sam remote test-event put ApiFunction --stack-name next-sam-dms-api --name aptean_create_todo --file ./events/create_todo.json
sam remote test-event put ApiFunction --stack-name next-sam-dms-api --name aptean_delete_todo --file ./events/delete_todo.json
sam remote test-event put ApiFunction --stack-name next-sam-dms-api --name aptean_get_todo_by_id --file ./events/get_todo_by_id.json
sam remote test-event put ApiFunction --stack-name next-sam-dms-api --name aptean_get_todos --file ./events/get_todos.json
sam remote test-event put ApiFunction --stack-name next-sam-dms-api --name aptean_update_todo --file ./events/update_todo.json

