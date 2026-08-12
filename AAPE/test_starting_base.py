"""
Test unitario para verificar que el agente siempre vuelve a su base inicial
sin importar cómo se llame la base.
"""
import sys
import json
from unittest.mock import Mock, MagicMock

# Importar las clases necesarias
import AAgent_BT
import Goals_BT_Basic


def test_internal_state_captures_starting_base():
    """Verifica que InternalState captura la base inicial correctamente."""
    print("Test 1: Captura de base inicial...")
    
    # Crear un InternalState
    i_state = AAgent_BT.InternalState()
    
    # Simular primer update con currentNamedLoc
    sensor_info = []
    i_state_dict = {
        "isRotatingRight": False,
        "isRotatingLeft": False,
        "movingForwards": False,
        "movingBackwards": False,
        "isFrozen": None,
        "speed": 0.0,
        "position": {"x": 0, "y": 0, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "currentNamedLoc": "BaseBeta",
        "onRoute": False,
        "targetNamedLoc": "",
        "myInventoryList": [],
        "nearbyContainerInventory": False,
        "nearbyContainerInventoryList": []
    }
    
    i_state.update_internal_state(sensor_info, i_state_dict)
    
    # Verificar que starting_base se capturó
    assert i_state.starting_base == "BaseBeta", f"Expected 'BaseBeta', got '{i_state.starting_base}'"
    print("✓ Base inicial capturada correctamente: 'BaseBeta'")
    
    # Verificar que no cambia en updates posteriores
    i_state_dict["currentNamedLoc"] = "OtherLocation"
    i_state.update_internal_state(sensor_info, i_state_dict)
    assert i_state.starting_base == "BaseBeta", "starting_base no debería cambiar después de capturarse"
    print("✓ Base inicial no cambia en updates posteriores")


def test_internal_state_captures_different_base_names():
    """Verifica que funciona con diferentes nombres de base."""
    print("\nTest 2: Diferentes nombres de base...")
    
    test_cases = [
        "BaseAlpha",
        "BaseStation3",
        "HomeBase",
        "SpawnPoint42",
        "CustomBaseName"
    ]
    
    for base_name in test_cases:
        i_state = AAgent_BT.InternalState()
        i_state_dict = {
            "isRotatingRight": False,
            "isRotatingLeft": False,
            "movingForwards": False,
            "movingBackwards": False,
            "isFrozen": None,
            "speed": 0.0,
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "currentNamedLoc": base_name,
            "onRoute": False,
            "targetNamedLoc": "",
            "myInventoryList": [],
            "nearbyContainerInventory": False,
            "nearbyContainerInventoryList": []
        }
        
        i_state.update_internal_state([], i_state_dict)
        assert i_state.starting_base == base_name, f"Expected '{base_name}', got '{i_state.starting_base}'"
        print(f"✓ Capturado correctamente: '{base_name}'")


def test_return_to_base_uses_starting_base():
    """Verifica que ReturnToBase usa el starting_base correcto."""
    print("\nTest 3: ReturnToBase usa starting_base...")
    
    # Crear un mock del agente
    mock_agent = Mock()
    mock_agent.AgentParameters = {"team": "Beta"}
    
    # Crear InternalState con starting_base
    i_state = AAgent_BT.InternalState()
    i_state_dict = {
        "isRotatingRight": False,
        "isRotatingLeft": False,
        "movingForwards": False,
        "movingBackwards": False,
        "isFrozen": None,
        "speed": 0.0,
        "position": {"x": 0, "y": 0, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "currentNamedLoc": "CustomBaseName",
        "onRoute": False,
        "targetNamedLoc": "",
        "myInventoryList": [],
        "nearbyContainerInventory": False,
        "nearbyContainerInventoryList": []
    }
    i_state.update_internal_state([], i_state_dict)
    
    mock_agent.i_state = i_state
    
    # Crear ReturnToBase
    return_to_base = Goals_BT_Basic.ReturnToBase(mock_agent)
    
    # Verificar que usa starting_base y no "Base" + team
    assert return_to_base.base_name == "CustomBaseName", \
        f"Expected 'CustomBaseName', got '{return_to_base.base_name}'"
    print(f"✓ ReturnToBase usa starting_base: '{return_to_base.base_name}'")
    
    # Verificar que NO usa el formato hardcodeado "Base" + team
    assert return_to_base.base_name != "BaseBeta", \
        "No debería usar el formato hardcodeado 'Base' + team"
    print("✓ No usa el formato hardcodeado 'Base' + team")


def test_empty_current_named_loc():
    """Verifica comportamiento cuando currentNamedLoc está vacío inicialmente."""
    print("\nTest 4: currentNamedLoc vacío inicialmente...")
    
    i_state = AAgent_BT.InternalState()
    
    # Primer update con currentNamedLoc vacío
    i_state_dict = {
        "isRotatingRight": False,
        "isRotatingLeft": False,
        "movingForwards": False,
        "movingBackwards": False,
        "isFrozen": None,
        "speed": 0.0,
        "position": {"x": 0, "y": 0, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "currentNamedLoc": "",
        "onRoute": False,
        "targetNamedLoc": "",
        "myInventoryList": [],
        "nearbyContainerInventory": False,
        "nearbyContainerInventoryList": []
    }
    
    i_state.update_internal_state([], i_state_dict)
    assert i_state.starting_base == "", "starting_base debería estar vacío"
    print("✓ starting_base vacío cuando currentNamedLoc está vacío")
    
    # Segundo update con currentNamedLoc con valor
    i_state_dict["currentNamedLoc"] = "BaseAlpha"
    i_state.update_internal_state([], i_state_dict)
    assert i_state.starting_base == "BaseAlpha", "Debería capturar la base cuando aparece"
    print("✓ Captura base cuando currentNamedLoc tiene valor")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST SUITE: Verificación de base inicial dinámica")
    print("=" * 60)
    
    try:
        test_internal_state_captures_starting_base()
        test_internal_state_captures_different_base_names()
        test_return_to_base_uses_starting_base()
        test_empty_current_named_loc()
        
        print("\n" + "=" * 60)
        print("✓ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print("\nEl agente ahora:")
        print("- Captura dinámicamente su base inicial desde los sensores")
        print("- Siempre vuelve a esa base específica")
        print("- Funciona sin importar cómo se llame la base en la competición")
        
    except AssertionError as e:
        print(f"\n✗ TEST FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
