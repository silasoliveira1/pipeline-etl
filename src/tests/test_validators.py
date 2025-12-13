import pandas as pd
import pytest
from src.common.validators import DataValidator

@pytest.fixture
def validator():
    return DataValidator()

def test_validate_products_removes_negative_prices(validator):
    df = pd.DataFrame({
        'product_id': [1, 2, 3],
        'price': [10.0, -5.0, 0.0]
    })
    
    result = validator.validate_products(df)
    
    assert len(result) == 1
    assert result.iloc[0]['product_id'] == 1

def test_validate_customers_checks_email_format(validator):
    df = pd.DataFrame({
        'customer_id': [1, 2],
        'email': ['valid@email.com', 'invalid-email']
    })
    
    result = validator.validate_customers(df)
    
    assert len(result) == 1
    assert result.iloc[0]['email'] == 'valid@email.com'

def test_validate_orders_checks_amount(validator):
    df = pd.DataFrame({
        'order_id': [1, 2],
        'total_amount': [100.50, -10.0]
    })
    
    result = validator.validate_orders(df)
    
    assert len(result) == 1
    assert result.iloc[0]['total_amount'] == 100.50
