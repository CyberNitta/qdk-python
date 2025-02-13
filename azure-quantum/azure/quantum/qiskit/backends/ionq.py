##
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
##
from typing import TYPE_CHECKING, Dict
from azure.quantum import __version__
from azure.quantum.target.ionq import IonQ
from abc import abstractmethod

from .backend import AzureBackend, AzureQirBackend

from qiskit.providers.models import BackendConfiguration
from qiskit.providers import Options, Provider

from qiskit_ionq.helpers import (
    ionq_basis_gates,
    GATESET_MAP,
    qiskit_circ_to_ionq_circ,
)

if TYPE_CHECKING:
    from azure.quantum.qiskit import AzureQuantumProvider

import logging

logger = logging.getLogger(__name__)

__all__ = [
    "IonQBackend",
    "IonQQPUBackend",
    "IonQSimulatorBackend",
    "IonQAriaBackend",
    "IonQQirBackend",
    "IonQSimulatorQirBackend",
    "IonQSimulatorNativeBackend",
    "IonQQPUQirBackend",
    "IonQQPUNativeBackend",
    "IonQAriaQirBackend",
    "IonQAriaNativeBackend",
]


class IonQQirBackendBase(AzureQirBackend):
    """Base class for interfacing with an IonQ QIR backend"""

    @abstractmethod
    def __init__(
        self, configuration: BackendConfiguration, provider: Provider = None, **fields
    ):
        super().__init__(configuration, provider, **fields)

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=500, targetCapability="BasicExecution")

    def _azure_config(self) -> Dict[str, str]:
        config = super()._azure_config()
        config.update(
            {
                "provider_id": "ionq",
            }
        )
        return config


class IonQSimulatorQirBackend(IonQQirBackendBase):
    backend_names = ("ionq.simulator",)

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ QIR Simulator backend"""

        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": True,
                "local": False,
                "coupling_map": None,
                "description": "IonQ simulator on Azure Quantum",
                "basis_gates": ionq_basis_gates,
                "memory": False,
                "n_qubits": 29,
                "conditional": False,
                "max_shots": None,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
            }
        )
        logger.info("Initializing IonQSimulatorQirBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQQPUQirBackend(IonQQirBackendBase):
    backend_names = ("ionq.qpu",)

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ QPU backend"""

        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": False,
                "local": False,
                "coupling_map": None,
                "description": "IonQ QPU on Azure Quantum",
                "basis_gates": ionq_basis_gates,
                "memory": False,
                "n_qubits": 11,
                "conditional": False,
                "max_shots": 10000,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
            }
        )
        logger.info("Initializing IonQQPUQirBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQAriaQirBackend(IonQQirBackendBase):
    backend_names = ("ionq.qpu.aria-1", "ionq.qpu.aria-2")

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ Aria QPU backend"""

        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": False,
                "local": False,
                "coupling_map": None,
                "description": "IonQ Aria QPU on Azure Quantum",
                "basis_gates": ionq_basis_gates,
                "memory": False,
                "n_qubits": 23,
                "conditional": False,
                "max_shots": 10000,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
            }
        )
        logger.info("Initializing IonQAriaQirBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQBackend(AzureBackend):
    """Base class for interfacing with an IonQ backend in Azure Quantum"""

    backend_name = None

    @abstractmethod
    def __init__(
        self, configuration: BackendConfiguration, provider: Provider = None, **fields
    ):
        super().__init__(configuration, provider, **fields)

    @classmethod
    def _default_options(cls):
        return Options(shots=500)

    def _azure_config(self) -> Dict[str, str]:
        return {
            "blob_name": "inputData",
            "content_type": "application/json",
            "provider_id": "ionq",
            "input_data_format": "ionq.circuit.v1",
            "output_data_format": "ionq.quantum-results.v1",
            "is_default": True,
        }

    def _prepare_job_metadata(self, circuit, **kwargs):
        _, _, meas_map = qiskit_circ_to_ionq_circ(circuit, gateset=self.gateset())

        metadata = super()._prepare_job_metadata(circuit, **kwargs)
        metadata["meas_map"] = meas_map

        return metadata

    def _translate_input(self, circuit):
        """Translates the input values to the format expected by the AzureBackend."""
        ionq_circ, _, _ = qiskit_circ_to_ionq_circ(circuit, gateset=self.gateset())
        input_data = {
            "gateset": self.gateset(),
            "qubits": circuit.num_qubits,
            "circuit": ionq_circ,
        }
        return IonQ._encode_input_data(input_data)

    def gateset(self):
        return self.configuration().gateset

    def estimate_cost(self, circuit, shots):
        """Estimate the cost for the given circuit."""
        ionq_circ, _, _ = qiskit_circ_to_ionq_circ(circuit, gateset=self.gateset())
        input_data = {
            "qubits": circuit.num_qubits,
            "circuit": ionq_circ,
        }
        workspace = self.provider().get_workspace()
        target = workspace.get_targets(self.name())
        return target.estimate_cost(input_data, num_shots=shots)


class IonQSimulatorBackend(IonQBackend):
    backend_names = ("ionq.simulator",)

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ Simulator backend"""
        gateset = kwargs.pop("gateset", "qis")
        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": True,
                "local": False,
                "coupling_map": None,
                "description": "IonQ simulator on Azure Quantum",
                "basis_gates": GATESET_MAP[gateset],
                "memory": False,
                "n_qubits": 29,
                "conditional": False,
                "max_shots": None,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
                "gateset": gateset,
            }
        )
        logger.info("Initializing IonQSimulatorBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQSimulatorNativeBackend(IonQSimulatorBackend):
    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        if "gateset" not in kwargs:
            kwargs["gateset"] = "native"
        super().__init__(name, provider, **kwargs)

    def _azure_config(self) -> Dict[str, str]:
        config = super()._azure_config()
        config.update(
            {
                "is_default": False,
            }
        )
        return config


class IonQQPUBackend(IonQBackend):
    backend_names = ("ionq.qpu",)

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ QPU backend"""
        gateset = kwargs.pop("gateset", "qis")
        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": False,
                "local": False,
                "coupling_map": None,
                "description": "IonQ QPU on Azure Quantum",
                "basis_gates": GATESET_MAP[gateset],
                "memory": False,
                "n_qubits": 11,
                "conditional": False,
                "max_shots": 10000,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
                "gateset": gateset,
            }
        )
        logger.info("Initializing IonQQPUBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQQPUNativeBackend(IonQQPUBackend):
    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        if "gateset" not in kwargs:
            kwargs["gateset"] = "native"
        super().__init__(name, provider, **kwargs)

    def _azure_config(self) -> Dict[str, str]:
        config = super()._azure_config()
        config.update(
            {
                "is_default": False,
            }
        )
        return config


class IonQAriaBackend(IonQBackend):
    backend_names = ("ionq.qpu.aria-1", "ionq.qpu.aria-2")

    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        """Base class for interfacing with an IonQ Aria QPU backend"""
        gateset = kwargs.pop("gateset", "qis")
        default_config = BackendConfiguration.from_dict(
            {
                "backend_name": name,
                "backend_version": __version__,
                "simulator": False,
                "local": False,
                "coupling_map": None,
                "description": "IonQ Aria QPU on Azure Quantum",
                "basis_gates": GATESET_MAP[gateset],
                "memory": False,
                "n_qubits": 23,
                "conditional": False,
                "max_shots": 10000,
                "max_experiments": 1,
                "open_pulse": False,
                "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
                "azure": self._azure_config(),
                "gateset": gateset,
            }
        )
        logger.info("Initializing IonQAriaQPUBackend")
        configuration: BackendConfiguration = kwargs.pop(
            "configuration", default_config
        )
        super().__init__(configuration=configuration, provider=provider, **kwargs)


class IonQAriaNativeBackend(IonQAriaBackend):
    def __init__(self, name: str, provider: "AzureQuantumProvider", **kwargs):
        if "gateset" not in kwargs:
            kwargs["gateset"] = "native"
        super().__init__(name, provider, **kwargs)

    def _azure_config(self) -> Dict[str, str]:
        config = super()._azure_config()
        config.update(
            {
                "is_default": False,
            }
        )
        return config
