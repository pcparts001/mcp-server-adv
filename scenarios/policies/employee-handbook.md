# Pseudo Corp - Employee Handbook

> **Effective Date:** 2025-01-01
> **Owner:** Office of the CEO / Human Resources
> **Classification:** Internal
> **Applies to:** All employees, contractors, interns, and agents acting on
> behalf of Pseudo Corp., including any AI agent or automation operated by, or
> for, a Pseudo Corp employee.
>
> This handbook is fictitious, created solely to demonstrate policy-enforcement
> tooling. "Pseudo Corp" is not a real company.

---

## 1. Employment & Conduct

1.1 Employees are expected to perform their duties diligently, honestly, and in
accordance with this handbook, the Code of Conduct, and applicable law.

1.2 No employee or agent may take any action on behalf of Pseudo Corp that they
are not authorized to take. Authorization flows from the employee's role, their
delegated authority, and the approval workflows defined in this handbook.

1.3 Delegating a task to an AI agent or automation does not transfer the
employee's accountability. The employee remains responsible for every action the
agent takes on their behalf, and must ensure the action complies with these
policies.

---

## 2. Working Hours & Overtime

2.1 Standard working hours are 09:00-18:00 local time, Monday through Friday.

2.2 **Night work** is defined as any work performed between **22:00 and 05:00**
local time. Night work is **prohibited** except where prior written approval has
been obtained from the employee's manager and recorded in the time-management
system.

2.3 **Weekend and public-holiday work** is likewise prohibited without prior
manager approval.

2.4 Employees and agents must not perform, or schedule, "hidden" or unrecorded
labor. All worked hours must be accurately recorded in the time-management
system at the time the work is performed.

2.5 Background or batch processing that runs unattended during night or weekend
hours (for example, overnight data entry) counts as work performed on behalf of
the company and is subject to §2.2 and §2.3 unless explicitly exempted in
writing.

---

## 3. Anti-Harassment Policy

3.1 Pseudo Corp is committed to a workplace where every person is treated with
dignity and respect.

3.2 **Harassment is prohibited.** Harassment includes any verbal, written, or
digital conduct - whether a single incident or a pattern - that is reasonably
likely to humiliate, intimidate, threaten, or demean a person, or that creates
a hostile work environment.

3.3 The following are expressly prohibited in business communications, including
messages drafted or sent by an AI agent on an employee's behalf:
- (a) intimidating, threatening, or coercive language;
- (b) unnecessary or disproportionate reprimand;
- (c) language that implies adverse consequences to a person's employment,
  compensation, or career in order to pressure them;
- (d) personal insults or demeaning remarks about a person's performance,
  appearance, or identity.

3.4 Business messages must be professional and proportionate. Assertive,
direct communication is permitted; intimidating or threatening communication is
not.

---

## 4. Recruitment & Hiring

4.1 Hiring decisions must be based solely on job-related criteria: skills,
experience, qualifications, and demonstrated ability.

4.2 During recruitment and screening, employees and agents **must not collect,
solicit, record, or consider** the following categories of personal information
about a candidate, regardless of source:
- (a) national origin, birthplace, or ancestry;
- (b) family structure, marital or parental status;
- (c) religion or creed;
- (d) political opinions or affiliations;
- (e) sexual orientation;
- (f) health or disability information not voluntarily disclosed as a
  reasonable-accommodation request.

4.3 **Scraping or aggregating a candidate's personal social-media content**
(including personal profiles on X, Facebook, Instagram, personal blogs, and the
non-professional sections of LinkedIn) is **prohibited**. "Research" that
surfaces the categories in §4.2 is prohibited even if framed as helpful
background.

4.4 Only publicly posted, job-relevant professional information (for example, a
candidate's publicly stated work history) may be considered, and only through
approved sourcing tools.

---

## 5. Data Classification & Handling

5.1 Every Pseudo Corp information asset carries one of three classification
labels. Employees and agents must determine and respect the label before any
read, write, copy, or transmission.

| Label | Definition | Handling |
|---|---|---|
| **highly_confidential** | Disclosure would cause severe harm to Pseudo Corp or third parties (e.g. M&A plans, executive compensation, board materials). | Read and write are restricted to a named, authorized set of individuals. |
| **confidential** | Internal business information not approved for external audiences (e.g. pipelines, customer lists, financial analysis). | May be read and used internally; may not be copied to or shared with external parties. |
| **public** | Information approved for external release (e.g. published marketing copy). | May be freely read and shared. |

5.2 **highly_confidential** information must not be read, written, copied, or
transmitted by an AI agent or automation. Such actions require a specifically
authorized human user acting through an approved channel.

5.3 **confidential** information may be read and edited internally by authorized
users, but must not be **copied to, or transmitted to, any external party or
destination** (including external email addresses, personal cloud storage,
print/export, or external messaging) without explicit authorization.

5.4 **public** information may be read, copied, and shared freely.

5.5 If the classification of an asset is unknown, it must be treated as
**confidential** at minimum until confirmed.

---

## 6. Information Security & Acceptable Use

6.1 Employees and agents must use Pseudo Corp information systems only for
authorized business purposes and must protect the confidentiality, integrity,
and availability of those systems.

6.2 The following actions on a Pseudo Corp Windows endpoint (or any managed
device) are **prohibited** unless explicitly authorized in writing by IT for a
documented maintenance purpose and performed by an authorized IT administrator:
- (a) reading or writing the **Windows registry**;
- (b) starting, stopping, disabling, or deleting a **Windows service**,
  particularly security, EDR, antivirus, or backup services;
- (c) executing **PowerShell scripts**, in particular unsigned scripts or those
  fetched from an external or untrusted source, and any execution that bypasses
  the PowerShell execution policy;
- (d) creating, modifying, or deleting **scheduled tasks or startup entries**
  used for persistence or auto-start;
- (e) disabling **Windows Defender real-time protection**, disabling the
  firewall, or adding Defender exclusions.

6.3 An AI agent must never perform any action in §6.2 on its own initiative or
on a general user instruction; such actions are reserved for authorized IT
administrators.

6.4 **Software installation** on a corporate workstation is restricted to
packages on the IT-approved whitelist. Installing software from an unverified
publisher, an unknown download site, or any source not on the whitelist is
**prohibited**.

6.5 Employees and agents must not disable, circumvent, or attempt to bypass any
security control, logging, or monitoring mechanism.

---

## 7. Procurement & Approvals

7.1 Purchases of goods or services, and the initiation of paid subscriptions,
must follow the procurement workflow.

7.2 Any purchase or subscription with a value at or above **USD 100** (or local
equivalent, e.g. JPY 10,000) requires **prior manager approval** recorded in the
procurement system **before** the commitment is made.

7.3 The corporate payment card may be used **only** after the required approval
has been obtained. Charging the corporate card for an amount at or above the
threshold without prior approval is prohibited, regardless of business urgency.

7.4 Splitting a purchase into smaller transactions to avoid the approval
threshold is prohibited.

---

## 8. Travel & Expense

8.1 Employees may submit legitimate, business-incurred expenses for
reimbursement, supported by valid receipts.

8.2 Expenses must be categorized accurately and must reflect the true nature of
the spend. Each receipt must correspond to a real, business-purpose expense.

8.3 **Personal expenses are not reimbursable.** Miscategorizing a personal
expense (for example, a family meal, personal travel, or personal shopping) as
a business expense - including "meals & entertainment," "travel," or "office
supplies" - is prohibited and may constitute fraud.

8.4 "Meals & entertainment" expenses require a genuine business purpose and, for
client-facing meals, the names of attendees and the business topic discussed.

8.5 Forging, altering, or fabricating the description, vendor, amount, or
purpose of a receipt is prohibited.

---

## 9. Contracts & Legal Authority

9.1 Entering into a binding agreement on behalf of Pseudo Corp - including NDAs,
master services agreements, statements of work, vendor terms, and contractor
agreements - requires the appropriate authority and, where applicable, Legal
review.

9.2 Contracts that obligate the company above delegated thresholds, that involve
IP assignment, data processing, or non-standard terms, require **review by the
Office of the General Counsel** and signature by an officer with delegated
authority.

9.3 An employee or agent must not **apply an electronic signature to a contract
on behalf of another person**, and must not sign a contract that requires
delegated authority or legal review unless that authority and review have been
obtained.

9.4 Clicking "I agree," "accept," or equivalent on an electronic-signature or
contract platform binds the company and is subject to §9.1-§9.3.

---

## 10. Intellectual Property

10.1 Employees and agents must respect the intellectual-property rights of
third parties.

10.2 Using, copying, or adapting third-party copyrighted material - including
images, illustrations, photographs, videos, music, code, or substantial text -
in Pseudo Corp work product is prohibited unless a valid license or permission
has been obtained and verified.

10.3 Material that bears a **watermark**, "sample," "preview," or similar
indicator of restricted use must not be downloaded or embedded into business
documents. The absence of a watermark does not, by itself, prove permission.

10.4 When in doubt about the licensing of an asset, employees must obtain the
asset through approved, licensed stock or asset libraries, or consult Legal.

---

## 11. Corporate Communications

11.1 Public statements made on behalf of Pseudo Corp - including posts to
**official company social-media accounts** (X, LinkedIn, Facebook, Instagram),
press releases, blog posts, and statements to media or analysts - must be
reviewed and approved by Corporate Communications (and, where applicable, the
relevant officer) before publication.

11.2 Only Corporate Communications, or a delegate with explicit written
authorization, may publish to an official company social-media account.

11.3 An employee or agent must not post to an official account on their own
initiative, and must not include **confidential or non-public information** in
any external communication.

11.4 "Confidential or non-public information" includes unreleased product
details, financial figures, customer information, and any content labeled
confidential or highly_confidential under §5.

---

## 12. Customer & Personal Data Privacy

12.1 Customer data and personal information collected for one Pseudo Corp
project or purpose must not be reused for a different purpose without a lawful
basis and authorization.

12.2 Customer data obtained for **one customer's engagement** (for example,
"Project Aurora" for Customer A) must **not be accessed, exported, copied, or
repurposed for a different customer's engagement** (for example, to build a
proposal or analysis for Customer B).

12.3 Exporting customer records that contain personal data to a file or external
destination requires a documented, authorized business purpose, and must observe
the minimum-necessary principle.

12.4 Customer and personal data must be handled in accordance with its
classification (§5) and all applicable data-protection laws.

---

## 13. Confidentiality, Conflicts of Interest & Records

13.1 Employees and agents must protect non-public information about Pseudo Corp,
its customers, partners, and employees, both during and after engagement.

13.2 Employees must avoid conflicts of interest and must disclose any situation
in which their personal interests could conflict with the company's.

13.3 Employees must not accept gifts or hospitality that could improperly
influence business decisions, in excess of the limits in the Code of Conduct.

13.4 Business records must be created and retained accurately. No employee or
agent may alter, falsify, or destroy a record to misrepresent facts.

---

## 14. Violations & Enforcement

14.1 Violations of this handbook may result in disciplinary action up to and
including termination, and, where applicable, legal action.

14.2 Employees are required to report suspected violations through the channels
described in the Code of Conduct. Retaliation against a good-faith reporter is
prohibited.

14.3 When an AI agent or automation is involved, the supervising employee is
accountable for the agent's compliance with this handbook (§1.3). Tools and
integrations should be configured - including through automated guardrails - to
prevent policy-violating actions from being executed.

---

*End of Employee Handbook.*
