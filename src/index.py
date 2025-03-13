import src.buckaroo_client as buckaroo_client

from uuid import uuid4

x = buckaroo_client.BuckarooClient(
    "EKkn4BByTj", "AB6176482E7B44C3BA7DB47F156088B5", "test"
)

x.payable("ideal").pay(
    {
        "amountDebit": 40.30,
        "order": str(uuid4()),
        "invoice": str(uuid4()),
        "trackAndTrace": "TR0F123456789",
        "vatNumber": "2",
    }
).execute()
