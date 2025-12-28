# JOVIAL J73 Language Server

Language Server Protocol (LSP) implementation for JOVIAL J73, the programming language defined by MIL-STD-1589C.

## What is JOVIAL?

**JOVIAL** (Jules' Own Version of the International Algebraic Language) was developed in 1959 by Jules Schwartz at System Development Corporation for US Air Force embedded systems. It remains in active use in critical military systems worldwide.

### Systems Still Running JOVIAL Code

- **Fighter Aircraft:** F-15, F-16 (pre-Block 50), F-117, F-111
- **Bombers:** B-52, B-1B, B-2 Spirit
- **Transport:** C-130, C-141, C-17
- **Surveillance:** E-3 AWACS, U-2
- **Naval:** Aegis cruisers
- **Missiles:** Advanced Cruise Missile, MLRS
- **Satellites:** Milstar
- **Other:** NORAD air defence, UH-60 Black Hawk

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
- Comments (quoted strings)
- String literals

## J73 Language Overview

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

### Key Constructs

```jovial
" This is a comment in JOVIAL "

START PROGRAM'NAME;

" Constants "
DEFINE MAX'SIZE = 100;

" Variables "
ITEM COUNTER STATIC S 16;
ITEM ALTITUDE F 32 = 0.0;

" Arrays/Structures "
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

## Installation

### VS Code Extension

1. Install the extension from the VS Code marketplace
2. Ensure Python 3.8+ is installed
3. Open any `.jov`, `.j73`, or `.jovial` file

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/jovial-lsp

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

- `.jov` - JOVIAL source file
- `.j73` - JOVIAL J73 source file
- `.cpl` - COMPOOL (shared data module)
- `.jovial` - JOVIAL source file (long form)

## Documentation Sources

This LSP was built using official JOVIAL documentation from the Defence Technical Information Centre (DTIC) and other authoritative sources:

### Standards
| Document | Description | Year |
|----------|-------------|------|
| **MIL-STD-1589C** | Official J73 language standard | 1984 |
| **DTIC ADA094930** | MIL-STD-1589B Draft standard | 1980 |

### Programming Manuals
| Document | Description | Year |
|----------|-------------|------|
| **DTIC ADA101061** | J73 Programming Manual - Combined tutorial and reference | 1981 |
| **DTIC ADA061714** | JOCIT - JOVIAL Compiler Implementation Tool | - |
| **DTIC ADA037637** | Language Evaluation: JOVIAL J3B vs ALGOL 68, PASCAL, SIMULA 67, TACPOL | 1977 |
| **DTIC ADA145697** | AFSC Avionics Standards Conference proceedings | 1982 |

### Tutorials
| Document | Description | Year |
|----------|-------------|------|
| **DTIC ADA142780** | J73 Tutorial - Programming language tutorial | 1982 |

All documents are available through the Defence Technical Information Centre (DTIC) and are preserved in my own historical computing archive.

## Language History

- **1959:** JOVIAL developed at SDC by Jules Schwartz
- **1973:** Standardised as MIL-STD-1589
- **1979:** MIL-STD-1589A revision
- **1980:** MIL-STD-1589B revision
- **1984:** MIL-STD-1589C (current standard)
- **2010:** USAF JOVIAL Programme Office (JPO) ceased active maintenance

Despite being "unmaintained" since 2010, JOVIAL code continues to fly in military aircraft and control weapon systems worldwide.

## Why This Matters

The programmers who wrote these systems are retiring. The documentation is disappearing. Modern developers need tools to understand, maintain, and eventually modernise these critical systems.

This LSP provides the foundation for:
- Understanding legacy JOVIAL codebases
- Training new maintainers
- Enabling code analysis and modernisation
- Preserving institutional knowledge

## Contributing

Contributions are welcome, particularly:
- Additional syntax patterns from real-world JOVIAL code
- Improved semantic analysis
- Integration with JOVIAL compilers
- Documentation corrections and additions

## Licence

Apache License 2.0 - See LICENSE file for details.

Copyright 2025 Zane Hambly

## Related Projects

If you've enjoyed writing code for aircraft that could, at any moment, be called upon to do something terribly important, you might also fancy:

- **[CMS-2 LSP](https://github.com/Zaneham/cms2-lsp)** - For the US Navy's tactical combat systems. Because the sea is also full of things that need precise timing and questionable documentation.

- **[CORAL 66 LSP](https://github.com/Zaneham/coral66-lsp)** - The British Ministry of Defence's real-time language. Developed between tea breaks at the Royal Radar Establishment, Malvern. Features Crown Copyright and a stiff upper lip.

- **[HAL/S LSP](https://github.com/Zaneham/hals-lsp)** - NASA's Space Shuttle language. For when you need your vectors and matrices handled by a computer that absolutely cannot restart mid-flight.

- **[Minuteman Guidance Computer Emulator](https://github.com/Zaneham/minuteman-emu)** - An emulator for the D17B/D37C computers that have been keeping 400 nuclear missiles pointed at things since 1962. I'm not entirely sure why I built this. Seemed like a good idea at the time.

- **[Minuteman Assembler](https://github.com/Zaneham/minuteman-assembler)** - Two-pass assembler for the D17B/D37C. For when the emulator wasn't enough and you needed a complete toolchain for nuclear missiles. Perfectly normal hobby.

## Acknowledgements

- Jules Schwartz - Creator of JOVIAL (1959)
- System Development Corporation
- US Air Force JOVIAL Programme Office
- Defence Technical Information Centre (DTIC)
- My grandad :-) 
