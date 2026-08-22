import re
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any

class Iso20022Engine:
    @staticmethod
    def parse_camt054_credit(xml_string: str) -> Dict[str, Any]:
        """Parses an inbound ISO 20022 camt.054.001.08 Credit Notification."""
        clean_xml = re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)
        root = ET.fromstring(clean_xml)

        ntfctn = root.find(".//Ntfctn")
        if ntfctn is None:
            raise ValueError("Invalid camt.054: Missing <Ntfctn> element.")

        msg_id = root.findtext(".//GrpHdr/MsgId", default="UNKNOWN-MSG-ID")
        ntry = ntfctn.find(".//Ntry")
        if ntry is None:
            raise ValueError("Invalid camt.054: Missing <Ntry> entry.")

        amt_elem = ntry.find("./Amt")
        amount = float(amt_elem.text) if amt_elem is not None else 0.0
        currency = amt_elem.attrib.get("Ccy", "USD") if amt_elem is not None else "USD"

        credit_debit = ntry.findtext("./CdtDbtInd", default="CRDT")
        booking_date = ntry.findtext(".//BookgDt/Dt", default=datetime.utcnow().strftime("%Y-%m-%d"))
        account_iban = ntfctn.findtext(".//Acct/Id/Othr/Id", default="UNKNOWN-ACCOUNT")

        raw_hash = hashlib.sha256(xml_string.encode('utf-8')).hexdigest()

        return {
            "message_id": msg_id,
            "account_identifier": account_iban,
            "amount": amount,
            "currency": currency,
            "direction": credit_debit,
            "booking_date": booking_date,
            "audit_merkle_hash": f"0x{raw_hash}",
            "status": "SETTLED"
        }

    @staticmethod
    def generate_pain001_payment(debtor_bban: str, creditor_bban: str, amount_usd: float, end_to_end_id: str) -> str:
        """Generates an outbound ISO 20022 pain.001.001.09 Credit Transfer Instruction."""
        msg_id = f"UNYKORN-PAIN001-{int(datetime.utcnow().timestamp())}"
        cre_dt = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.09">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{cre_dt}</CreDtTm>
      <NbOfTxs>1</NbOfTxs>
      <InitgPty>
        <Nm>Unykorn Fiduciary Gateway LLC</Nm>
      </InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMT-INFO-{end_to_end_id}</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>{datetime.utcnow().strftime("%Y-%m-%d")}</ReqdExctnDt>
      <Dbtr>
        <Nm>SPV Fiduciary Escrow Reserve</Nm>
      </Dbtr>
      <DbtrAcct>
        <Id>
          <Othr>
            <Id>{debtor_bban}</Id>
          </Othr>
        </Id>
      </DbtrAcct>
      <DbtrAgt>
        <FinInstnId>
          <Nm>Charter Bank &amp; Trust, NA</Nm>
        </FinInstnId>
      </DbtrAgt>
      <CdtTrfTxInf>
        <PmtId>
          <EndToEndId>{end_to_end_id}</EndToEndId>
        </PmtId>
        <Amt>
          <InstdAmt Ccy="USD">{amount_usd:.2f}</InstdAmt>
        </Amt>
        <Cdtr>
          <Nm>Institutional Debt/Equity Investor</Nm>
        </Cdtr>
        <CdtrAcct>
          <Id>
            <Othr>
              <Id>{creditor_bban}</Id>
            </Othr>
          </Id>
        </CdtrAcct>
        <RmtInf>
          <Ustrd>Quarterly Yield Distribution - SPV Clean Energy Debt Tranche A</Ustrd>
        </RmtInf>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""
        return xml_template
