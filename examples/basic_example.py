from gerg_type_validation import (assert_string_like,TypeAssertionError,create_lenient_engine,
                                  ValidationContext,schema_validator,SchemaValidator,ValidationPatterns,
                                  BatchValidator,assert_sequence,assert_type)

if __name__ == "__main__":
    # Example 1a: Basic usage with default engine
    try:
        name = "John Doe"
        validated_name = assert_string_like(name, min_len=1, max_len=50)
        print(f"Valid name: {validated_name}")
    except TypeAssertionError as e:
        print(f"Validation error: {e}")


    # Example 1b: Baic usage with custom type
    class Person:
        name:str

        def __init__(self,name) -> None:
            self.name = name

        def __str__(self) -> str:
            return f"Person(name={self.name})"

    try:
        person = Person(name="John Doe")
        validated_person = assert_type(person,expected_type=Person)
        print(f"Valid person: {validated_person}")
    except TypeAssertionError as e:
        print(f"Validation error: {e}")

    # Example 2: Using custom engine with different configuration
    lenient_engine = create_lenient_engine()

    with ValidationContext(lenient_engine, raise_on_failure=True):
        try:
            age = "not a number"
            validated_age = lenient_engine.assert_numeric(age, min_val=0, max_val=150)
        except TypeAssertionError as e:
            print(f"Age validation failed: {e}")

    # Example 3: Schema validation
    schema_validator = SchemaValidator()
    user_schema = {
        'name': {'type': str, 'required': True},
        'age': {'type': int, 'required': True, 'validator': lambda x: ValidationPatterns.validate_non_negative_number(x)},
        'email': {'type': str, 'required': False, 'validator': ValidationPatterns.validate_email}
    }

    user_data = {
        'name': 'Alice',
        'age': 30,
        'email': 'alice@example.com'
    }

    try:
        validated_user = schema_validator.validate_dict_schema(user_data, user_schema)
        print(f"Valid user data: {validated_user}")
    except TypeAssertionError as e:
        print(f"Schema validation failed: {e}")

    # Example 4: Batch validation
    batch = BatchValidator()
    batch.add_validation("test@email.com", ValidationPatterns.validate_email)
    batch.add_validation(25, ValidationPatterns.validate_positive_number)
    batch.add_validation([1, 2, 3], assert_sequence, min_len=1, max_len=5)

    if batch.validate_all(raise_on_error=False):
        print("All batch validations passed!")
    else:
        print(f"Batch validation errors: {batch.get_errors()}")