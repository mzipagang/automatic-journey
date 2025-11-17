# PyTest Quickstart Guide

## Test Structure
pytest does not require any specific file structure.  As long as you postfix (or Prefix) your filename with _test.py (example_test.py), it will automatically find your tests.  That being said, we'd like to standardize how we structure our tests, so that all teams have a similar pattern.  Tests will be kept in a ___tests___ folder off of the root directory.  Inside, tests will be organized by the type of test the test file contains (unit, api, ui).

- tests
    - pycache
    - init.py
    - unit
        - test_example.py 
        - test_jwt.py
    - api
        - test_api.py
    - ui
        - test_ui.py


## Running Tests
|  Use Case | Command |
|---|---|
| Run all test files | pytest |
| Run with increased Verbosity | pytest -v ( --verbose ) |
| Run with the built-in Debugger | pytest --pdb |
| Run Specific Tests by Substring | pytest -k ___SubString___ -v |
| Show standard output even for passing tests (Default is only failed tests) | pytest -s |
| Stop test run after FIRST failed Test | pytest -x ( --exitfirst ) |
| Show Help - All args and usages | pytest -h |



## Assertions
|  Method  |    Checks  |
|---|---|
| assert ___expression___ | expression validates |
| assertEqual(a, b) | a == b |
| assertNotEqual(a, b) | a != b |
| assertTrue(x) | bool(x) is True |
| assertFalse(x) | bool(x) is False |
| assertIs(a, b) | a is b |
| assertIsNot(a, b) | a is not b |
| assertIsNone(x) | x is None |
| assertIsNotNone(x) | x is not None |
| assertIn(a, b) | a in b |
| assertNotIn(a, b) | a not in b |
| assertIsInstance(a, b) | isInstance(a, b) |
| assertNotIsInstance(a, b) | not isInstance(a, b) |
| assertRaises(exc, fun, args, *kwds) | fun(*args, **kwds) raises exc |
| assertRaisesRegexp(exc, r, fun, args, *kwds) | round(a-b, 7) == 0 |
| assertAlmostEqual(a, b) |  round(a-b, 7) == 0 |
| assertNotAlmostEqual(a, b) | round(a-b, 7) != 0 |
| assertGreater(a, b) | a > b |
| assertGreaterEqual(a, b) | a >= b |
| assertLess(a, b) | a < b |
| assertLessEqual(a, b) | a <= b |
| assertRegexpMatches(a, b) | b.search(a) |
| assertNotRegexpMatches(a, b) | not b.search(a) |
| assertItemsEqual(a, b) | sorted(a) == sorted(b) |
| assertDictContainsSubset(a, b) | All key/value pairs in a exist in b |

All assert methods, except assertRaises() and assertRaisesRegexp(), accept a ___msg___ argument that is used as the error message on failure



## Grouping Tests
You can group tests into classes.  Be sure to prefix the class name with ___Test___, otherwise the class will be skipped.
```
    class TestClass:
        def test_one(self):
            x = "this"
            assert "h" in x

        def test_two(self):
            x = "hello"
            assert hasattr(x, "check")
```


## Fixtures
Pytest fixtures are functions that can be used to manage our apps states and dependencies. Most importantly, they can provide data for testing and a wide range of value types when explicitly called by our testing software. You can use the mock data that fixtures create across multiple tests.
```
    @pytest.fixture
    def userName():
        return 'Dude McDuderson'
```
This fixture can then be reused in multiple tests.  This is a VERY simple example, but should give you an idea of what you COULD do with Fixtures.
```
    def test_read_main(self):
        client = TestClient(app)
        response = client.get("/example?name='{}'".format(userName))
        assert response.status_code == 200
```


## Mock / MonkeyPatch modules and environments
Sometimes tests need to invoke functionality which depends on global settings or which invokes code which cannot be easily tested such as network access. The monkeypatch fixture helps you to safely set/delete an attribute, dictionary item or environment variable, or to modify sys.path for importing.

The monkeypatch fixture provides these helper methods for safely patching and mocking functionality in tests:
* monkeypatch.setattr(obj, name, value, raising=True)
* monkeypatch.delattr(obj, name, raising=True)
* monkeypatch.setitem(mapping, name, value)
* monkeypatch.delitem(obj, name, raising=True)
* monkeypatch.setenv(name, value, prepend=None)
* monkeypatch.delenv(name, raising=True)
* monkeypatch.syspath_prepend(path)
* monkeypatch.chdir(path)
* monkeypatch.context()


## Test Coverage
Coverage is included in the workflow template but you can follow these steps to run coverage locally.
- install pytest-cov
    - __pip install pytest-cov__
- Run pytest with coverage
    - __pytest --cov=app tests/__



## References
| How To | Link |
|---|---|
| PyTest Docs | https://docs.pytest.org/en/7.1.x/index.html |
| Fixtures | https://docs.pytest.org/en/7.1.x/how-to/fixtures.html |
| Fixture Examples | https://www.testim.io/blog/using-pytest-fixtures/#:~:text=What%20Are%20Pytest%20Fixtures%3F,fixtures%20create%20across%20multiple%20tests |
| PyTest Mock | https://pytest-mock.readthedocs.io/en/latest/ |
| Monkeypatch | https://docs.pytest.org/en/7.1.x/how-to/monkeypatch.html |