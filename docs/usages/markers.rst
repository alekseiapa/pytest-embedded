##################
 Addition Markers
##################

``pytest-embedded`` provides additional markers to enhance testing functionality.

*****************
 ``skip_if_soc``
*****************

The ``skip_if_soc`` marker allows you to skip tests based on the ``soc_caps`` (system-on-chip capabilities) of a target device. These capabilities are defined in the ``esp-idf``. For example, for the ESP32, you can reference them in the ``soc_caps.h`` file: `soc_caps.h <https://github.com/espressif/esp-idf/blob/master/components/soc/esp32/include/soc/soc_caps.h>`_.

Use Case
========

Imagine you have multiple targets, such as ``[esp32, esp32c3, ..., esp32s4]``. However, you may want to skip tests for chips that do not support specific features.

The ``skip_if_soc`` marker simplifies this by allowing you to define conditions based on the ``soc_caps`` property of your chip. This enables dynamic filtering of targets without the need for manual target-specific logic.

Examples
========

Here are examples of how to use ``skip_if_soc`` with different conditions:

**Condition 1**: A boolean expression such as ``SOC_ULP_SUPPORTED != 1 and SOC_UART_NUM != 3``. This skips tests for chips that:

   -  Do not support the ``low power mode`` feature (``SOC_ULP_SUPPORTED != 1``).
   -  **And** have a UART number other than 3 (``SOC_UART_NUM != 3``).

.. code:: python

   @pytest.mark.skip_if_soc("SOC_ULP_SUPPORTED != 1 and SOC_UART_NUM != 3")
   @pytest.mark.parametrize("target", ["esp32", "esp32s2", "esp32c3"], indirect=True)
   def test_template_first_condition():
       pass

----

**Condition 2**: A boolean expression such as ``SOC_ULP_SUPPORTED != 1 or SOC_UART_NUM != 3``. This skips tests for chips that:

   -  Either do not support the ``low power mode`` feature (``SOC_ULP_SUPPORTED != 1``).
   -  **Or** have a UART number other than 3 (``SOC_UART_NUM != 3``).

.. code:: python

   @pytest.mark.skip_if_soc("SOC_ULP_SUPPORTED != 1 or SOC_UART_NUM != 3")
   @pytest.mark.parametrize("target", ["esp32", "esp32s2", "esp32c3"], indirect=True)
   def test_template_second_condition():
       pass

----

**Condition 3**: You can use a shortcut to apply this condition to all ESP-IDF supported targets (assuming ``IDF_PATH`` is set).

.. code:: python

   import pytest
   from esp_bool_parser.constants import SUPPORTED_TARGETS

   @pytest.mark.skip_if_soc("SOC_ULP_SUPPORTED != 1")
   @pytest.mark.parametrize("target", SUPPORTED_TARGETS, indirect=True)
   def test_template():
       pass
