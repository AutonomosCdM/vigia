"""
Tests for Slack Block Kit Medical Components
Validates Block Kit structure and HIPAA compliance
"""
import pytest
from datetime import datetime
from vigia_detect.slack.block_kit_medical import BlockKitMedical, BlockKitInteractions
from vigia_detect.core.constants import TEST_PATIENT_DATA


class TestBlockKitMedical:
    """Test Block Kit medical components"""
    
    def test_lpp_alert_blocks_structure(self):
        """Test LPP alert block structure"""
        blocks = BlockKitMedical.lpp_alert_blocks(
            case_id="TEST_001",
            patient_code="PAT001",
            lpp_grade=2,
            confidence=0.85,
            location="sacrum",
            service="UCI",
            bed="201A"
        )
        
        # Validate block structure
        assert isinstance(blocks, list)
        assert len(blocks) >= 6  # Header, patient info, detection, description, actions, context
        
        # Check header block
        header_block = blocks[0]
        assert header_block["type"] == "header"
        assert "LPP Grado 2" in header_block["text"]["text"]
        assert "URGENTE" in header_block["text"]["text"]
        
        # Check action block exists
        action_blocks = [b for b in blocks if b.get("type") == "actions"]
        assert len(action_blocks) == 1
        
        action_block = action_blocks[0]
        assert len(action_block["elements"]) == 3  # Ver Historial, Evaluación, Marcar Resuelto
        
        # Validate button actions
        buttons = action_block["elements"]
        assert any("Ver Historial" in btn["text"]["text"] for btn in buttons)
        assert any("Evaluación Médica" in btn["text"]["text"] for btn in buttons)
        assert any("Marcar Resuelto" in btn["text"]["text"] for btn in buttons)
    
    def test_lpp_alert_hipaa_compliance(self):
        """Test HIPAA compliance in LPP alerts"""
        blocks = BlockKitMedical.lpp_alert_blocks(
            case_id="CASE_001",
            patient_code="PATIENT_FULL_NAME_123",
            lpp_grade=3,
            confidence=0.92,
            location="heel",
            service="Emergency",
            bed="ROOM_505_BED_A"
        )
        
        # Extract all text content
        all_text = self._extract_all_text(blocks)
        
        # Should contain anonymized patient info
        assert "PAT***" in all_text  # Anonymized patient
        assert "RO***" in all_text   # Anonymized bed
        
        # Should NOT contain full identifiers
        assert "PATIENT_FULL_NAME_123" not in all_text
        assert "ROOM_505_BED_A" not in all_text
        
        # Should contain HIPAA compliance reference
        assert "HIPAA" in all_text or "Compliant" in all_text
    
    def test_patient_history_blocks_structure(self):
        """Test patient history block structure"""
        blocks = BlockKitMedical.patient_history_blocks(TEST_PATIENT_DATA)
        
        # Validate structure
        assert isinstance(blocks, list)
        assert len(blocks) >= 6  # Header, demographics, diagnoses, medications, lpp history, context
        
        # Check header
        header_block = blocks[0]
        assert header_block["type"] == "header"
        assert "Historial Médico" in header_block["text"]["text"]
        
        # Check sections exist
        section_blocks = [b for b in blocks if b.get("type") == "section"]
        assert len(section_blocks) >= 5  # Demographics, diagnoses, medications, lpp history, care notes
        
        # Validate content structure
        all_text = self._extract_all_text(blocks)
        assert "Diagnósticos" in all_text
        assert "Medicamentos" in all_text
        assert "Historial de LPP" in all_text
    
    def test_case_resolution_modal_structure(self):
        """Test case resolution modal structure"""
        modal = BlockKitMedical.case_resolution_modal("CASE_123")
        
        # Validate modal structure
        assert modal["type"] == "modal"
        assert modal["callback_id"] == "case_resolution_CASE_123"
        assert "title" in modal
        assert "submit" in modal
        assert "close" in modal
        assert "blocks" in modal
        
        # Check required form elements
        blocks = modal["blocks"]
        input_blocks = [b for b in blocks if b.get("type") == "input"]
        assert len(input_blocks) >= 3  # Description, time, followup
        
        # Validate input types
        input_types = []
        for block in input_blocks:
            element = block["element"]
            input_types.append(element["type"])
        
        assert "plain_text_input" in input_types  # Description
        assert "static_select" in input_types     # Time selection
        assert "checkboxes" in input_types        # Followup options
    
    def test_medical_evaluation_request_blocks(self):
        """Test medical evaluation request blocks"""
        blocks = BlockKitMedical.medical_evaluation_request_blocks("CASE_456", "critical")
        
        # Validate structure
        assert isinstance(blocks, list)
        assert len(blocks) >= 4
        
        # Check critical urgency styling
        header_block = blocks[0]
        assert "🚨" in header_block["text"]["text"]
        assert "CRÍTICA" in header_block["text"]["text"]
        
        # Check action buttons
        action_blocks = [b for b in blocks if b.get("type") == "actions"]
        assert len(action_blocks) == 1
        
        buttons = action_blocks[0]["elements"]
        assert len(buttons) >= 3
        assert any("Aceptar Evaluación" in btn["text"]["text"] for btn in buttons)
    
    def test_system_error_blocks(self):
        """Test system error notification blocks"""
        error_data = {
            "component": "lpp_detector",
            "code": "ERR_001",
            "severity": "high",
            "message": "Model inference failed"
        }
        
        blocks = BlockKitMedical.system_error_blocks(error_data)
        
        # Validate structure
        assert isinstance(blocks, list)
        assert len(blocks) >= 4
        
        # Check error information
        all_text = self._extract_all_text(blocks)
        assert "ERR_001" in all_text
        assert "lpp_detector" in all_text
        assert "Model inference failed" in all_text
        
        # Check action buttons
        action_blocks = [b for b in blocks if b.get("type") == "actions"]
        assert len(action_blocks) == 1
    
    def test_severity_styling(self):
        """Test different LPP grades have appropriate styling"""
        # Test Grade 1 (low severity)
        blocks_1 = BlockKitMedical.lpp_alert_blocks(
            "CASE1", "PAT1", 1, 0.7, "heel", "Ward", "101A"
        )
        
        # Test Grade 4 (critical severity)
        blocks_4 = BlockKitMedical.lpp_alert_blocks(
            "CASE4", "PAT4", 4, 0.95, "sacrum", "ICU", "401A"
        )
        
        # Grade 4 should have more urgent styling
        text_1 = self._extract_all_text(blocks_1)
        text_4 = self._extract_all_text(blocks_4)
        
        # Grade 4 should contain critical indicators
        assert "Grado 4" in text_4
        # Both should be urgent but Grade 4 should be more emphasized
        assert "URGENTE" in text_1
        assert "URGENTE" in text_4
    
    def _extract_all_text(self, blocks: list) -> str:
        """Extract all text content from blocks for testing"""
        text_parts = []
        
        for block in blocks:
            if block.get("type") == "header":
                text_parts.append(block.get("text", {}).get("text", ""))
            
            elif block.get("type") == "section":
                # Section text
                if "text" in block:
                    text_parts.append(block["text"].get("text", ""))
                
                # Section fields
                if "fields" in block:
                    for field in block["fields"]:
                        text_parts.append(field.get("text", ""))
            
            elif block.get("type") == "context":
                for element in block.get("elements", []):
                    text_parts.append(element.get("text", ""))
            
            elif block.get("type") == "actions":
                for element in block.get("elements", []):
                    if element.get("type") == "button":
                        text_parts.append(element.get("text", {}).get("text", ""))
        
        return " ".join(text_parts)


class TestBlockKitInteractions:
    """Test Block Kit interaction handlers"""
    
    def test_handle_view_medical_history_action(self):
        """Test view medical history action handling"""
        response = BlockKitInteractions.handle_action(
            "view_medical_history_CASE_123",
            "CASE_123",
            "USER_456"
        )
        
        assert response["response_type"] == "ephemeral"
        assert "CASE_123" in response["text"]
        assert "Historial médico" in response["text"] and "solicitado" in response["text"]
        assert "blocks" in response
    
    def test_handle_request_medical_evaluation_action(self):
        """Test request medical evaluation action handling"""
        response = BlockKitInteractions.handle_action(
            "request_medical_evaluation_CASE_789",
            "CASE_789",
            "USER_123"
        )
        
        assert response["response_type"] == "ephemeral"
        assert "CASE_789" in response["text"]
        assert "Evaluación médica solicitada" in response["text"]
        assert "blocks" in response
        
        # Should return medical evaluation request blocks
        blocks = response["blocks"]
        assert len(blocks) >= 4
    
    def test_handle_mark_resolved_action(self):
        """Test mark resolved action handling"""
        response = BlockKitInteractions.handle_action(
            "mark_resolved_CASE_456",
            "CASE_456",
            "USER_789"
        )
        
        assert response["response_type"] == "ephemeral"
        assert "CASE_456" in response["text"]
        assert "resolución" in response["text"]
    
    def test_handle_modal_submission(self):
        """Test modal form submission handling"""
        modal_data = {
            "callback_id": "case_resolution_CASE_123",
            "state": {
                "values": {
                    "resolution_description": {
                        "description_input": {
                            "value": "Lesión tratada con éxito, paciente estable"
                        }
                    },
                    "resolution_time": {
                        "time_select": {
                            "selected_option": {
                                "value": "1hr"
                            }
                        }
                    },
                    "followup_required": {
                        "followup_checkboxes": {
                            "selected_options": [
                                {"value": "medical_followup"},
                                {"value": "notify_specialist"}
                            ]
                        }
                    }
                }
            }
        }
        
        response = BlockKitInteractions.handle_modal_submission(modal_data)
        
        assert response["response_action"] == "update"
        assert response["view"]["type"] == "modal"
        assert "Caso Resuelto" in response["view"]["title"]["text"]
        
        # Check that case info is in the response
        blocks = response["view"]["blocks"]
        text_content = " ".join([
            block.get("text", {}).get("text", "") for block in blocks
            if block.get("type") == "section"
        ])
        assert "CASE_123" in text_content
        assert "resuelto" in text_content
    
    def test_unknown_action_handling(self):
        """Test handling of unknown action IDs"""
        response = BlockKitInteractions.handle_action(
            "unknown_action_123",
            "some_value",
            "USER_456"
        )
        
        # Should return default response for unknown actions
        assert response["response_type"] == "ephemeral"
        assert "Procesando acción" in response["text"]


@pytest.mark.integration
class TestBlockKitIntegration:
    """Integration tests for Block Kit with real Slack-like scenarios"""
    
    def test_full_lpp_workflow(self):
        """Test complete LPP detection workflow with Block Kit"""
        # 1. Generate LPP alert
        alert_blocks = BlockKitMedical.lpp_alert_blocks(
            case_id="WORKFLOW_001",
            patient_code="WF_PAT_001",
            lpp_grade=3,
            confidence=0.88,
            location="coccyx",
            service="ICU",
            bed="ICU_401"
        )
        
        assert len(alert_blocks) >= 6
        
        # 2. Simulate button click for medical history
        history_response = BlockKitInteractions.handle_action(
            "view_medical_history_WORKFLOW_001",
            "WORKFLOW_001",
            "NURSE_123"
        )
        
        assert "WORKFLOW_001" in history_response["text"]
        
        # 3. Generate resolution modal
        resolution_modal = BlockKitMedical.case_resolution_modal("WORKFLOW_001")
        
        assert resolution_modal["callback_id"] == "case_resolution_WORKFLOW_001"
        
        # 4. Simulate modal submission
        submission_response = BlockKitInteractions.handle_modal_submission({
            "callback_id": "case_resolution_WORKFLOW_001",
            "state": {
                "values": {
                    "resolution_description": {
                        "description_input": {"value": "Test resolution"}
                    },
                    "resolution_time": {
                        "time_select": {
                            "selected_option": {"value": "30min"}
                        }
                    },
                    "followup_required": {
                        "followup_checkboxes": {
                            "selected_options": []
                        }
                    }
                }
            }
        })
        
        assert submission_response["response_action"] == "update"
        assert "WORKFLOW_001" in str(submission_response)
    
    def test_anonymization_consistency(self):
        """Test that anonymization is consistent across all Block Kit components"""
        # Test data with identifiable information
        test_patient = {
            'id': 'FULL_PATIENT_ID_12345',
            'name': 'FULL_PATIENT_NAME',
            'age': 65,
            'service': 'Cardiology',
            'bed': 'ROOM_305_BED_B'
        }
        
        # Generate patient history blocks
        history_blocks = BlockKitMedical.patient_history_blocks(test_patient)
        history_text = self._extract_all_text_from_blocks(history_blocks)
        
        # Generate LPP alert blocks
        alert_blocks = BlockKitMedical.lpp_alert_blocks(
            "CASE_001",
            "FULL_PATIENT_NAME",
            2, 0.8, "sacrum", "Cardiology", "ROOM_305_BED_B"
        )
        alert_text = self._extract_all_text_from_blocks(alert_blocks)
        
        # Both should be anonymized consistently
        assert "FULL_PATIENT_ID_12345" not in history_text
        assert "FULL_PATIENT_NAME" not in history_text and "FULL_PATIENT_NAME" not in alert_text
        assert "ROOM_305_BED_B" not in alert_text
        
        # Should contain anonymized versions
        assert "***" in history_text  # Anonymization marker
        assert "***" in alert_text     # Anonymization marker
    
    def _extract_all_text_from_blocks(self, blocks: list) -> str:
        """Helper to extract all text from blocks"""
        text_parts = []
        for block in blocks:
            if block.get("type") == "header":
                text_parts.append(block.get("text", {}).get("text", ""))
            elif block.get("type") == "section":
                if "text" in block:
                    text_parts.append(block["text"].get("text", ""))
                if "fields" in block:
                    for field in block["fields"]:
                        text_parts.append(field.get("text", ""))
        return " ".join(text_parts)