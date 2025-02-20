from pydantic import Field, BaseModel
from typing import List


class FinalReport(BaseModel):
    """Write the detailed forensic analysis reports concluding the analysis."""
    detailed_report: str = Field(...)
    cve_identifier: str = Field(...)
    affected_service: str = Field(...)
    successfull_attack: bool = Field(...)
    is_vulnerable: bool = Field(...)
    #critical_pcap_items: List = Field(...)

    def run(self):
        final_report = f'FINAL REPORT:\n'
        final_report += self.detailed_report
        final_report += f'\nREPORT SUMMARY:\n'
        final_report += f'Identified CVE: {self.cve_identifier}\n'
        final_report += f'Affected Service: {self.affected_service}\n'
        final_report += f'Is Service Vulnerable: {self.is_vulnerable}\n'
        if self.successfull_attack:
            final_report += f'Attack: Succeeded\n'
        else:
            final_report += f'Attack: Failed\n'
        #criticalities = '\n'.join([f'*{x}' for x in self.critical_pcap_items])
        #final_report += f'Critical PCAP entries: {criticalities}'
        
        return final_report


class FinalAnswer(BaseModel):
    """Provide the correctly detected CVE"""
    cve_identifier: str = Field(...)
