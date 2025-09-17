"""
Example: IdealQr Payment Method Usage

This example demonstrates how to use the IdealQr payment method with the Buckaroo SDK.
IdealQr generates QR codes for iDEAL payments in the Netherlands.
"""

from buckaroo._buckaroo_client import BuckarooClient
from datetime import date, datetime, timedelta


def main():
    # Initialize the Buckaroo client
    client = BuckarooClient("your_store_key", "your_secret_key")
    
    print("=== IdealQr Payment Examples ===\n")
    
    # Example 1: Basic IdealQr payment using fluent interface
    print("1. Basic IdealQr Payment (Fluent Interface):")
    
    basic_payment = (client.payments.create_payment("idealqr")
                    .description("Coffee and pastry")
                    .purchase_id("CAFE_001_" + str(int(datetime.now().timestamp())))
                    .amount(4.50))
    
    print("   Payment Request JSON:")
    result = basic_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 2: Advanced IdealQr payment with all parameters
    print("2. Advanced IdealQr Payment (All Parameters):")
    
    expiration_date = date.today() + timedelta(days=30)
    
    advanced_payment = (client.payments.create_payment("idealqr")
                       .description("Premium subscription")
                       .min_amount(0.10)
                       .max_amount(100.0)
                       .image_size(2000)
                       .purchase_id("SUB_PREM_" + str(int(datetime.now().timestamp())))
                       .is_one_off(False)  # Recurring payment
                       .amount(19.99)
                       .amount_is_changeable(True)
                       .expiration(expiration_date)
                       .is_processing(True))
    
    print("   Payment Request JSON:")
    result = advanced_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 3: IdealQr payment using dictionary parameters
    print("3. IdealQr Payment (Dictionary Parameters):")
    
    qr_params = {
        'qr_description': 'Online book purchase',
        'purchase_id': f'BOOK_{int(datetime.now().timestamp())}',
        'amount': 24.99,
        'min_amount': 1.00,
        'max_amount': 50.00,
        'image_size': 1500,
        'is_one_off': True,
        'amount_is_changeable': False,
        'expiration': '2024-12-31',
        'is_processing': False
    }
    
    dict_payment = client.payments.create_payment("idealqr", qr_params)
    
    print("   Payment Request JSON:")
    result = dict_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 4: Combined dictionary and fluent interface
    print("4. Combined Dictionary + Fluent Interface:")
    
    base_params = {
        'qr_description': 'Base description',
        'purchase_id': f'COMBO_{int(datetime.now().timestamp())}',
        'amount': 10.00
    }
    
    combined_payment = (client.payments.create_payment("idealqr", base_params)
                       .description("Enhanced description")  # Override
                       .min_amount(5.00)  # Add new
                       .max_amount(25.00)  # Add new
                       .image_size(2500)  # Add new
                       .amount_is_changeable(True))  # Add new
    
    print("   Payment Request JSON:")
    result = combined_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 5: Custom QR parameters
    print("5. Custom QR Parameters:")
    
    custom_payment = (client.payments.create_payment("idealqr")
                     .description("Custom QR payment")
                     .purchase_id(f'CUSTOM_{int(datetime.now().timestamp())}')
                     .amount(15.75))
    
    # Add custom parameters using the low-level method
    custom_payment.add_qr_parameter("CustomField1", "CustomValue1", "CustomGroup", "Group1")
    custom_payment.add_qr_parameter("CustomField2", "CustomValue2", "CustomGroup", "Group2")
    
    print("   Payment Request JSON:")
    result = custom_payment.build()
    print(f"   {result.to_json()}\n")
    
    # Example 6: Demonstration of execution (mock)
    print("6. Payment Execution Example:")
    
    execution_payment = (client.payments.create_payment("idealqr")
                        .description("Execution test")
                        .purchase_id(f'EXEC_{int(datetime.now().timestamp())}')
                        .amount(5.00))
    
    try:
        # This would normally send the request to Buckaroo
        result = execution_payment.execute()
        print(f"   Execution result: {result}")
    except Exception as e:
        print(f"   Execution would send request to Buckaroo API")
        print(f"   (In this example: {e})")
    
    print("\n=== IdealQr Integration Tips ===")
    print("• IdealQr generates QR codes for iDEAL payments")
    print("• Use 'Generate' action to create QR codes")
    print("• QR codes can be displayed to customers for scanning")
    print("• Supports both one-off and recurring payments")
    print("• Image size controls QR code resolution (pixels)")
    print("• Expiration date limits QR code validity")
    print("• Amount can be changeable to allow customer input")
    print("• Min/max amounts set payment boundaries")


if __name__ == "__main__":
    main()