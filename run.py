"""Source-checkout launcher; also works when macOS hides editable-install .pth files."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    from vidrobust.cli import main
    main()
