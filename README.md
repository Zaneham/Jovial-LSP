# JOVIAL J73 Language Server

[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/ZaneHambly.jovial-lsp?label=VS%20Code%20Marketplace)](https://marketplace.visualstudio.com/items?itemName=ZaneHambly.jovial-lsp)

Language Server Protocol (LSP) implementation for **JOVIAL J73**, the programming language that has been flying fighter jets since your grandparents were dating.

## What is JOVIAL?

In 1959, a programmer named Jules Schwartz at System Development Corporation needed a language for US Air Force embedded systems. He called it **JOVIAL**—"Jules' Own Version of the International Algebraic Language." This is the kind of naming confidence that only existed before marketing departments were invented.

Jules was right to be confident. Sixty-five years later, JOVIAL code is still flying:

### Systems Still Running JOVIAL Code

| Category | Systems |
|----------|---------|
| **Fighter Aircraft** | F-15 Eagle, F-16 Fighting Falcon (pre-Block 50), F-117 Nighthawk, F-111 Aardvark |
| **Bombers** | B-52 Stratofortress, B-1B Lancer, B-2 Spirit |
| **Transport** | C-130 Hercules, C-141 Starlifter, C-17 Globemaster |
| **Surveillance** | E-3 AWACS, U-2 Dragon Lady |
| **Naval** | Aegis cruisers |
| **Missiles** | Advanced Cruise Missile, MLRS |
| **Satellites** | Milstar |
| **Command & Control** | NORAD air defence, UH-60 Black Hawk |

When an F-15 pilot pulls the trigger, JOVIAL code handles what happens next. When a B-52 needs to know where it is over the Pacific, JOVIAL code tells it. When NORAD tracks something entering North American airspace, JOVIAL code is part of that decision chain.

The US Air Force officially stopped maintaining JOVIAL in 2010. The aircraft kept flying. The code keeps running. Nobody has time to rewrite it, and frankly, it works.

## Features

### Code Intelligence
- **Completion:** Context-aware suggestions for keywords, ITEMs, TABLEs, PROCs
- **Hover:** Type information and documentation on hover
- **Go to Definition:** Jump to ITEM, TABLE, and PROC declarations
- **Find References:** Find all uses of a symbol
- **Document Symbols:** Outline view of all declarations

### Syntax Highlighting
- Keywords and control flow
- Type declarations (S, U, F, A, B, C, STATUS)
- STATUS values V(name)
- Comments (quoted strings, because JOVIAL predates the semicolon wars)
- String literals

## J73 Language Overview

JOVIAL uses single-character type abbreviations because when you're writing avionics code on 1960s hardware, every byte matters. Also, the programmers were busy. Fighter jets to build.

### Type Abbreviations

| Type | Description | Example |
|------|-------------|---------|
| `S` | Signed integer | `ITEM COUNT S 16;` |
| `U` | Unsigned integer | `ITEM FLAGS U 8;` |
| `F` | Floating point | `ITEM TEMP F 32;` |
| `A` | Fixed point (scaled) | `ITEM RATE A 16 D 4;` |
| `B` | Bit string | `ITEM MASK B 8;` |
| `C` | Character string | `ITEM NAME C 30;` |
| `P` | Pointer | `ITEM PTR P;` |
| `STATUS` | Enumeration | `ITEM MODE STATUS (V(ON), V(OFF));` |

### Sample Code

```jovial
" This is a comment in JOVIAL "
" Yes, comments are just quoted strings "
" Jules had opinions "

START PROGRAM'NAME;

" Constants "
DEFINE MAX'SIZE = 100;

" Variables - note the apostrophe in names "
" This was considered good practice in 1959 "
ITEM COUNTER STATIC S 16;
ITEM ALTITUDE F 32 = 0.0;

" Arrays and Structures "
TABLE DATA (1: MAX'SIZE);
BEGIN
    ITEM VALUE F 32;
    ITEM VALID B 1;
END

" Procedures "
PROC COMPUTE (INPUT : OUTPUT);
BEGIN
    ITEM INPUT S;
    ITEM OUTPUT S;
    OUTPUT := INPUT * 2;
END

TERM
```

The apostrophe-in-names convention (`MAX'SIZE`, `PROGRAM'NAME`) was JOVIAL's solution to readable identifiers before camelCase or snake_case were invented. It looks strange now. It made perfect sense in 1959.

## Installation

### VS Code Extension

1. Install the extension from the VS Code marketplace
2. Ensure Python 3.8+ is installed
3. Open any `.jov`, `.j73`, or `.jovial` file
4. Congratulations, you can now read F-15 avionics code

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/Zaneham/jovial-lsp

# Install dependencies
cd jovial-lsp
npm install

# Compile TypeScript
npm run compile

# Install in VS Code
code --install-extension jovial-lsp-1.0.0.vsix
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `jovial.pythonPath` | `python` | Path to Python interpreter |
| `jovial.serverPath` | (bundled) | Path to custom LSP server |
| `jovial.trace.server` | `off` | LSP communication tracing |

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.jov` | JOVIAL source file |
| `.j73` | JOVIAL J73 source file |
| `.cpl` | COMPOOL (shared data module) |
| `.jovial` | JOVIAL source file (for the unabbreviated) |

## Documentation Sources

This LSP was built using official JOVIAL documentation from the Defence Technical Information Centre (DTIC). These documents are preserved because someone at DTIC understood that software archaeology is a real discipline.

### Standards

| Document | Description | Year |
|----------|-------------|------|
| **MIL-STD-1589C** | Official J73 language standard | 1984 |
| **DTIC ADA094930** | MIL-STD-1589B Draft standard | 1980 |

### Programming Manuals

| Document | Description | Year |
|----------|-------------|------|
| **DTIC ADA101061** | J73 Programming Manual | 1981 |
| **DTIC ADA061714** | JOCIT — JOVIAL Compiler Implementation Tool | — |
| **DTIC ADA037637** | Language Evaluation: JOVIAL J3B vs ALGOL 68, PASCAL, SIMULA 67, TACPOL | 1977 |

### Tutorials

| Document | Description | Year |
|----------|-------------|------|
| **DTIC ADA142780** | J73 Tutorial | 1982 |

The 1977 language evaluation (ADA037637) is particularly entertaining. The Air Force seriously considered replacing JOVIAL with Pascal or ALGOL 68. They didn't. The F-15 was already flying.

## Language History

- **1959:** Jules Schwartz develops JOVIAL at SDC. Names it after himself. Correctly.
- **1973:** Standardised as MIL-STD-1589. The military discovers JOVIAL exists.
- **1979:** MIL-STD-1589A. The standard gets updated.
- **1980:** MIL-STD-1589B. The standard gets updated again.
- **1984:** MIL-STD-1589C. The current standard. Forty years old.
- **2010:** US Air Force JOVIAL Programme Office ceases active maintenance.
- **2025:** Fighter jets continue flying. JOVIAL continues running.

The fourteen-year gap between "we stopped maintaining this" and "but everything still works" is not a bug. It's a testament to the original engineering.

## Why This Matters

The engineers who wrote F-15 avionics in the 1970s are now in their seventies and eighties. Their knowledge exists in their heads, in retirement communities, in memories that fade a little more each year. The documentation lives in filing cabinets, DTIC archives, and boxes in hangars that haven't been opened since the Cold War ended.

But the aircraft keep flying. And someone needs to maintain the code.

This LSP exists because if you're the poor soul tasked with updating a B-52's mission computer in 2025, you shouldn't have to do it in vi with no syntax highlighting.

The foundation for:
- Understanding legacy JOVIAL codebases
- Training new maintainers (yes, they exist)
- Enabling code analysis and modernisation
- Preserving institutional knowledge before it's gone

## Contributing

Contributions are welcome, particularly:
- Additional syntax patterns from real-world JOVIAL code
- Improved semantic analysis
- Integration with JOVIAL compilers (if you have access to one)
- Documentation corrections from people who were there

## Licence

Apache License 2.0 — See LICENSE file for details.

Copyright 2025 Zane Hambly

## Related Projects

If you've enjoyed providing tooling for aircraft that could, at any moment, be called upon to do something terribly important, you might also appreciate:

- **[CMS-2 LSP](https://github.com/Zaneham/cms2-lsp)** — The US Navy's tactical combat systems language. Same era, different element. Aegis tracking instead of F-15 avionics.

- **[CORAL 66 LSP](https://github.com/Zaneham/coral66-lsp)** — British Ministry of Defence real-time language. Tornado aircraft and Royal Navy vessels. Developed at Malvern, presumably between tea breaks.

- **[HAL/S LSP](https://github.com/Zaneham/hals-lsp)** — NASA's Space Shuttle language. For when atmospheric flight isn't challenging enough.

- **[MUMPS LSP](https://github.com/Zaneham/mumps-lsp)** — The language running hospital systems. 305 million patient records. Different kind of life-critical.

- **[Minuteman Guidance Computer Emulator](https://github.com/Zaneham/minuteman-emu)** — An emulator for ICBM guidance computers. I'm not entirely sure why I built this. Seemed important at the time.

## Contact

Found a bug? Want to discuss the finer points of MIL-STD-1589C? Just want to tell someone you still write JOVIAL and have them believe you?

zanehambly@gmail.com — Response time faster than a B-52 answers to Strategic Command.

## Acknowledgements

- Jules Schwartz — Creator of JOVIAL (1959). Named a language after himself. It's still flying.
- System Development Corporation
- US Air Force JOVIAL Programme Office
- Defence Technical Information Centre (DTIC)
- My grandad, who encouraged me to put my stuff out there :-)
