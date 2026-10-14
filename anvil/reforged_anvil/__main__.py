"""`python -m reforged_anvil`: the desktop app, or the command line when given arguments."""
import sys

if len(sys.argv) > 1:
    from .cli import main
    sys.exit(main())
else:
    from .app import main
    main()
