# Real-project demo artifacts

Pinned Glamsterdam readiness demo outputs for grant review and reproducibility.

| Demo | Commit | Action run | Notes |
|------|--------|------------|-------|
| [transmissions11/solmate](transmissions11-solmate/89365b880c4f3c786bdd453d4b8e8fe410344a69/README.md) | `89365b880c4f3c786bdd453d4b8e8fe410344a69` | [run #27331627981](https://github.com/PXLabs-code/AISolidityAuditor/actions/runs/27331627981) | 5 Slither + 106 readiness findings |

Refresh locally:

```bash
python scripts/run_real_project_demo.py --demo transmissions11-solmate
```

Run the GitHub Actions demo workflow:

```bash
gh workflow run real-project-demo.yml -f demo=transmissions11-solmate
```
