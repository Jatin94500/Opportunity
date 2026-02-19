# Opportunity OS - Complete Architecture Diagrams

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow Architecture](#3-data-flow-architecture)
4. [Blockchain Integration](#4-blockchain-integration)
5. [Training Workflow](#5-training-workflow)
6. [UI Component Structure](#6-ui-component-structure)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Security Architecture](#8-security-architecture)

---

## 1. System Overview

```mermaid
graph TB
    subgraph "User Layer"
        USER[👤 User]
        BROWSER[🌐 Web Browser]
    end
    
    subgraph "Opportunity OS"
        subgraph "UI Layer"
            DEMO[NeuroChain Demo<br/>PyQt6 Application]
            SHELL[Opportunity Shell<br/>PySide6 Desktop]
        end
        
        subgraph "Core Layer"
            WALLET[Algorand Wallet<br/>Manager]
            TRAINER[AI Trainer<br/>Engine]
            RANKING[Ranking System<br/>& Rewards]
            BLOCKCHAIN[Blockchain<br/>Integration]
        end
        
        subgraph "Infrastructure Layer"
            DAEMON[Rust Daemon<br/>Hardware Monitor]
            WORKER[AI Worker<br/>Cython Engine]
            STORAGE[Local Storage<br/>JSON/Files]
        end
    end
    
    subgraph "External Services"
        ALGORAND[Algorand TestNet<br/>algonode.cloud]
        DATASETS[Dataset Storage<br/>CSV Files]
        GPU[GPU Hardware<br/>NVIDIA/AMD]
    end
    
    USER --> DEMO
    USER --> SHELL
    DEMO --> WALLET
    DEMO --> TRAINER
    SHELL --> WALLET
    SHELL --> DAEMON
    
    WALLET --> BLOCKCHAIN
    BLOCKCHAIN --> ALGORAND
    
    TRAINER --> DATASETS
    TRAINER --> GPU
    TRAINER --> RANKING
    
    DAEMON --> GPU
    DAEMON --> WORKER
    
    RANKING --> STORAGE
    WALLET --> STORAGE
    
    style USER fill:#6C63FF
    style ALGORAND fill:#00F5FF
    style GPU fill:#FF6B9D
```


---

## 2. Component Architecture

```mermaid
graph TB
    subgraph "NeuroChain Demo Application"
        subgraph "UI Components"
            MAIN_WIN[Main Window<br/>NeuroChainApp]
            DASHBOARD[Dashboard Page]
            TRAINING[Training Page]
            LOGS[Logs Page]
            NETWORK[Network Page]
            
            WALLET_CARD[Wallet Cards]
            CHART[Live Chart<br/>PyQtGraph]
            TASK_TABLE[Task Marketplace<br/>Table]
            METRICS[Metric Cards]
        end
        
        subgraph "Business Logic"
            NEUROCHAIN[NeuroChain<br/>Blockchain Simulator]
            AI_TRAINER[AITrainer<br/>ML Engine]
            RANK_SYS[RankingSystem<br/>Tier Manager]
            WORKER_THREAD[TrainingWorker<br/>QThread]
        end
        
        subgraph "Data Models"
            BLOCK[Block<br/>Blockchain Data]
            TASK[Task<br/>Training Jobs]
            WALLET_STATE[Wallet State<br/>Balance/Profit]
        end
    end
    
    subgraph "Opportunity Shell"
        subgraph "Shell UI"
            SHELL_WIN[OpportunityShellWindow]
            BOOT[Boot Screen]
            LOCK[Lock Screen]
            DESKTOP[Desktop Screen]
        end
        
        subgraph "Shell Core"
            DAEMON_CLIENT[Daemon Client<br/>IPC]
            ALGO_WALLET[AlgorandWallet<br/>Core]
        end
    end
    
    subgraph "Shared Infrastructure"
        WALLET_SYNC[Wallet State Sync<br/>JSON File]
        DATASETS_DIR[Datasets Directory<br/>CSV Files]
        KEYSTORE[Keystore<br/>Mnemonic Storage]
    end
    
    MAIN_WIN --> DASHBOARD
    MAIN_WIN --> TRAINING
    MAIN_WIN --> LOGS
    MAIN_WIN --> NETWORK
    
    DASHBOARD --> WALLET_CARD
    DASHBOARD --> CHART
    DASHBOARD --> TASK_TABLE
    DASHBOARD --> METRICS
    
    TRAINING --> WORKER_THREAD
    WORKER_THREAD --> AI_TRAINER
    AI_TRAINER --> DATASETS_DIR
    
    NEUROCHAIN --> BLOCK
    NEUROCHAIN --> TASK
    NEUROCHAIN --> RANK_SYS
    
    RANK_SYS --> WALLET_STATE
    WALLET_STATE --> WALLET_SYNC
    
    SHELL_WIN --> BOOT
    SHELL_WIN --> LOCK
    SHELL_WIN --> DESKTOP
    
    DESKTOP --> DAEMON_CLIENT
    SHELL_WIN --> ALGO_WALLET
    ALGO_WALLET --> KEYSTORE
    
    style MAIN_WIN fill:#6C63FF
    style SHELL_WIN fill:#6C63FF
    style ALGO_WALLET fill:#00F5FF
```


---

## 3. Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant UI as UI Layer
    participant Trainer as AI Trainer
    participant Ranking as Ranking System
    participant Wallet as Wallet Manager
    participant Blockchain as Algorand API
    participant Storage as Local Storage
    
    User->>UI: Start Training Task
    UI->>UI: Select Task from Marketplace
    
    UI->>Trainer: Initialize Training
    Trainer->>Storage: Load Dataset (CSV)
    Storage-->>Trainer: Return Dataset
    
    loop 10 Epochs
        Trainer->>Trainer: Train Neural Network
        Trainer->>UI: Update Progress (Epoch, Loss, Acc)
        UI->>UI: Update Chart & Metrics
    end
    
    Trainer->>Trainer: Generate Rival Scores
    Trainer->>Ranking: Submit Results
    
    Ranking->>Ranking: Calculate Rank & Payout
    alt Rank 1 (Winner)
        Ranking->>Ranking: Payout = 90% of Bounty
    else Rank 2 (Runner-up)
        Ranking->>Ranking: Payout = 10% of Bounty
    else Rank 3+ (Loss)
        Ranking->>Ranking: Payout = -0.05 ALGO
    end
    
    Ranking->>Wallet: Update Balance
    Wallet->>Storage: Publish Wallet State (JSON)
    
    opt Future: Blockchain Transaction
        Wallet->>Blockchain: Submit Transaction
        Blockchain-->>Wallet: Confirmation
    end
    
    Wallet->>UI: Update Display
    UI->>User: Show Results & Earnings
```


---

## 4. Blockchain Integration

```mermaid
graph TB
    subgraph "Application Layer"
        APP[Opportunity OS<br/>Application]
        WALLET_UI[Wallet UI<br/>Components]
    end
    
    subgraph "Wallet Core Module"
        WALLET_CLASS[AlgorandWallet Class]
        
        subgraph "Wallet Operations"
            CREATE[Create Wallet<br/>generate_account]
            LOAD[Load Wallet<br/>from JSON]
            BALANCE[Get Balance<br/>account_info]
            SIGN[Sign Transaction<br/>Future]
        end
        
        subgraph "Key Management"
            MNEMONIC[Mnemonic<br/>25-word phrase]
            PRIVATE_KEY[Private Key<br/>Derived]
            ADDRESS[Public Address<br/>ALGO Address]
        end
    end
    
    subgraph "Algorand SDK Layer"
        ALGOSDK[py-algorand-sdk]
        
        subgraph "SDK Modules"
            ACCOUNT_MOD[account module]
            MNEMONIC_MOD[mnemonic module]
            ALGOD_CLIENT[algod.AlgodClient]
            TRANSACTION[transaction module]
        end
    end
    
    subgraph "Network Layer"
        TESTNET[Algorand TestNet<br/>testnet-api.algonode.cloud]
        MAINNET[Algorand MainNet<br/>mainnet-api.algonode.cloud]
    end
    
    subgraph "Storage Layer"
        KEYSTORE[keystore.json<br/>data/keystore.json]
        WALLET_STATE[wallet_state.json<br/>runtime/opportunity_wallet_state.json]
    end
    
    APP --> WALLET_UI
    WALLET_UI --> WALLET_CLASS
    
    WALLET_CLASS --> CREATE
    WALLET_CLASS --> LOAD
    WALLET_CLASS --> BALANCE
    WALLET_CLASS --> SIGN
    
    CREATE --> ACCOUNT_MOD
    CREATE --> MNEMONIC_MOD
    LOAD --> MNEMONIC_MOD
    BALANCE --> ALGOD_CLIENT
    SIGN --> TRANSACTION
    
    ACCOUNT_MOD --> ALGOSDK
    MNEMONIC_MOD --> ALGOSDK
    ALGOD_CLIENT --> ALGOSDK
    TRANSACTION --> ALGOSDK
    
    CREATE --> MNEMONIC
    MNEMONIC --> PRIVATE_KEY
    PRIVATE_KEY --> ADDRESS
    
    MNEMONIC --> KEYSTORE
    ADDRESS --> KEYSTORE
    BALANCE --> WALLET_STATE
    
    ALGOD_CLIENT --> TESTNET
    ALGOD_CLIENT -.Future.-> MAINNET
    
    style ALGOSDK fill:#00F5FF
    style TESTNET fill:#34C759
    style MAINNET fill:#FF4D5A
    style KEYSTORE fill:#FF6B9D
```


---

## 5. Training Workflow

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> SelectTask: User Clicks Task
    SelectTask --> InitTraining: Activate Node
    
    InitTraining --> LoadDataset: Initialize Worker Thread
    LoadDataset --> PrepareData: Load CSV
    PrepareData --> TrainModel: Split Train/Test
    
    state TrainModel {
        [*] --> Epoch1
        Epoch1 --> Epoch2: Update Metrics
        Epoch2 --> Epoch3: Update Metrics
        Epoch3 --> EpochN: ...
        EpochN --> [*]: Complete
    }
    
    TrainModel --> GenerateRivals: Training Complete
    GenerateRivals --> CalculateRank: Simulate Competition
    
    state CalculateRank {
        [*] --> CompareAccuracy
        CompareAccuracy --> Rank1: Top Accuracy
        CompareAccuracy --> Rank2: Second Place
        CompareAccuracy --> Rank3Plus: Lower Ranks
        
        Rank1 --> PayoutWin: 90% Bounty
        Rank2 --> PayoutBreakeven: 10% Bounty
        Rank3Plus --> PayoutLoss: -0.05 ALGO
        
        PayoutWin --> [*]
        PayoutBreakeven --> [*]
        PayoutLoss --> [*]
    }
    
    CalculateRank --> UpdateWallet: Apply Payout
    UpdateWallet --> UpdateRanking: Update Balance
    UpdateRanking --> PublishState: Calculate Tier
    PublishState --> UpdateUI: Write JSON
    UpdateUI --> Idle: Display Results
    
    InitTraining --> Stopped: User Stops
    TrainModel --> Stopped: User Stops
    Stopped --> Idle: Reset
    
    note right of TrainModel
        Each epoch:
        - Partial fit on training data
        - Calculate accuracy on test data
        - Emit progress signals to UI
        - Update live chart
    end note
    
    note right of CalculateRank
        Ranking determines:
        - XP gain
        - Tier progression
        - Wallet balance change
        - Block mining (if winner)
    end note
```


---

## 6. UI Component Structure

```mermaid
graph TB
    subgraph "Main Application Window"
        MAIN[NeuroChainApp<br/>QMainWindow]
        
        subgraph "Top Bar"
            BRAND[Brand Logo]
            STATUS[Status Indicator]
            BAL_TOP[Balance Display<br/>ALGO]
        end
        
        subgraph "Sidebar"
            LOGO[Atom Logo]
            NAV_DASH[Dashboard Icon]
            NAV_TRAIN[Training Icon]
            NAV_LOGS[Logs Icon]
            NAV_NET[Network Icon]
            NAV_PROFILE[Profile Icon]
        end
        
        subgraph "Page Header"
            PAGE_TITLE[Page Title]
            METRIC_PROFIT[Total Profit Metric]
            METRIC_BEST[Best Model Metric]
            METRIC_SCORE[Node Score Metric]
        end
        
        subgraph "Content Area - QStackedWidget"
            subgraph "Dashboard Page"
                subgraph "Left Column"
                    WALLET_GROWTH[Wallet Growth Card<br/>Image Background]
                    WALLET_BALANCE[Wallet Balance Card<br/>Sparkline Chart]
                end
                
                subgraph "Center Column"
                    CHART_CARD[Training Metrics Chart<br/>PyQtGraph]
                    ASSETS_CARD[Available Tasks Table<br/>Marketplace]
                end
                
                subgraph "Right Column"
                    STATS_CARD[Node Stats Card<br/>GPU/Temp/VRAM]
                    ACTIVITY_CARD[Live Compute Card<br/>Queue/Rewards]
                end
            end
            
            subgraph "Training Page"
                CONTROL_PANEL[Node Control Panel<br/>Start/Stop/Register]
            end
            
            subgraph "Logs Page"
                TERMINAL[System Logs Terminal<br/>Scrollable]
            end
            
            subgraph "Network Page"
                NETWORK_STATS[Network Statistics]
                BLOCKS_TABLE[Recent Blocks Table]
            end
        end
    end
    
    MAIN --> BRAND
    MAIN --> STATUS
    MAIN --> BAL_TOP
    
    MAIN --> LOGO
    MAIN --> NAV_DASH
    MAIN --> NAV_TRAIN
    MAIN --> NAV_LOGS
    MAIN --> NAV_NET
    MAIN --> NAV_PROFILE
    
    MAIN --> PAGE_TITLE
    MAIN --> METRIC_PROFIT
    MAIN --> METRIC_BEST
    MAIN --> METRIC_SCORE
    
    NAV_DASH --> WALLET_GROWTH
    NAV_DASH --> WALLET_BALANCE
    NAV_DASH --> CHART_CARD
    NAV_DASH --> ASSETS_CARD
    NAV_DASH --> STATS_CARD
    NAV_DASH --> ACTIVITY_CARD
    
    NAV_TRAIN --> CONTROL_PANEL
    NAV_LOGS --> TERMINAL
    NAV_NET --> NETWORK_STATS
    NAV_NET --> BLOCKS_TABLE
    
    style MAIN fill:#6C63FF
    style WALLET_GROWTH fill:#FF6B9D
    style WALLET_BALANCE fill:#FF6B9D
    style CHART_CARD fill:#34C759
```


---

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_MACHINE[Developer Machine]
        
        subgraph "Python Virtual Environment"
            VENV[.venv/]
            PY_DEPS[Dependencies<br/>PySide6, algosdk, numpy, etc.]
        end
        
        subgraph "Source Code"
            DEMO_PY[neurochain_demo.py]
            SHELL_PY[dig_os/ui_shell/]
            WALLET_PY[core/wallet.py]
            DAEMON_RS[rust_daemon/]
        end
        
        subgraph "Data Files"
            DATASETS[datasets/]
            FONTS[fonts/]
            IMAGES[images/]
        end
    end
    
    subgraph "Build Pipeline"
        PYINSTALLER[PyInstaller<br/>Bundler]
        SPEC_FILES[.spec Files<br/>Build Config]
        
        subgraph "Build Artifacts"
            DIST[dist/]
            BUILD[build/]
            PAYLOAD[payload.zip]
        end
    end
    
    subgraph "Distribution"
        INSTALLER[Windows Installer<br/>NuroChainSetup.exe]
        
        subgraph "Installed Application"
            INSTALL_DIR[C:\Program Files\NuroChain\]
            EXE[neurochain.exe]
            RUNTIME_DATA[data/<br/>keystore.json]
            RUNTIME_STATE[runtime/<br/>wallet_state.json]
        end
    end
    
    subgraph "External Services"
        TESTNET_API[Algorand TestNet<br/>testnet-api.algonode.cloud]
        MAINNET_API[Algorand MainNet<br/>mainnet-api.algonode.cloud]
    end
    
    DEV_MACHINE --> VENV
    VENV --> PY_DEPS
    
    DEV_MACHINE --> DEMO_PY
    DEV_MACHINE --> SHELL_PY
    DEV_MACHINE --> WALLET_PY
    DEV_MACHINE --> DAEMON_RS
    
    DEV_MACHINE --> DATASETS
    DEV_MACHINE --> FONTS
    DEV_MACHINE --> IMAGES
    
    DEMO_PY --> PYINSTALLER
    SHELL_PY --> PYINSTALLER
    SPEC_FILES --> PYINSTALLER
    
    PYINSTALLER --> DIST
    PYINSTALLER --> BUILD
    PYINSTALLER --> PAYLOAD
    
    PAYLOAD --> INSTALLER
    
    INSTALLER --> INSTALL_DIR
    INSTALL_DIR --> EXE
    INSTALL_DIR --> RUNTIME_DATA
    INSTALL_DIR --> RUNTIME_STATE
    
    EXE --> TESTNET_API
    EXE -.Future.-> MAINNET_API
    
    style PYINSTALLER fill:#6C63FF
    style INSTALLER fill:#34C759
    style TESTNET_API fill:#00F5FF
```


---

## 8. Security Architecture

```mermaid
graph TB
    subgraph "User Space"
        USER[User]
        UI[Application UI]
    end
    
    subgraph "Application Security Layer"
        subgraph "Authentication"
            NO_AUTH[No Authentication<br/>⚠️ Current State]
            FUTURE_AUTH[Password/PIN<br/>✅ Future]
        end
        
        subgraph "Key Management"
            KEYSTORE[Keystore File<br/>data/keystore.json]
            
            subgraph "Current Implementation"
                PLAINTEXT[Plaintext Storage<br/>⚠️ Security Risk]
                JSON_FILE[JSON Format<br/>address + mnemonic]
            end
            
            subgraph "Future Implementation"
                ENCRYPTION[AES-256 Encryption<br/>✅ Planned]
                OS_KEYCHAIN[OS Keychain<br/>✅ Planned]
                HARDWARE_WALLET[Hardware Wallet<br/>✅ Planned]
            end
        end
        
        subgraph "Transaction Security"
            NO_TX[No Transactions<br/>Read-Only]
            FUTURE_TX[Transaction Signing<br/>✅ Future]
            CONFIRMATION[User Confirmation<br/>✅ Future]
        end
    end
    
    subgraph "Network Security"
        HTTPS[HTTPS Only<br/>✅ Enforced]
        TLS[TLS 1.2+<br/>✅ Certificate Validation]
        
        subgraph "API Endpoints"
            TESTNET[testnet-api.algonode.cloud<br/>Public Node]
            MAINNET[mainnet-api.algonode.cloud<br/>Public Node]
            CUSTOM[Custom Node<br/>Optional]
        end
    end
    
    subgraph "Data Security"
        subgraph "Local Storage"
            FILE_PERMS[File Permissions<br/>⚠️ Needs chmod 600]
            BACKUP[No Backup<br/>⚠️ User Responsibility]
        end
        
        subgraph "In-Memory"
            PRIVATE_KEY_MEM[Private Key in RAM<br/>⚠️ Cleared on Exit]
            MNEMONIC_MEM[Mnemonic in RAM<br/>⚠️ Temporary]
        end
    end
    
    subgraph "Threat Model"
        THREATS[Identified Threats]
        
        T1[File System Access<br/>Malware/Ransomware]
        T2[Memory Dump<br/>Debugger Attach]
        T3[Network MITM<br/>DNS Spoofing]
        T4[Phishing<br/>Fake Wallet UI]
    end
    
    USER --> UI
    UI --> NO_AUTH
    NO_AUTH -.Upgrade.-> FUTURE_AUTH
    
    UI --> KEYSTORE
    KEYSTORE --> PLAINTEXT
    KEYSTORE --> JSON_FILE
    
    PLAINTEXT -.Upgrade.-> ENCRYPTION
    PLAINTEXT -.Upgrade.-> OS_KEYCHAIN
    PLAINTEXT -.Upgrade.-> HARDWARE_WALLET
    
    UI --> NO_TX
    NO_TX -.Upgrade.-> FUTURE_TX
    FUTURE_TX --> CONFIRMATION
    
    UI --> HTTPS
    HTTPS --> TLS
    TLS --> TESTNET
    TLS --> MAINNET
    TLS --> CUSTOM
    
    KEYSTORE --> FILE_PERMS
    KEYSTORE --> BACKUP
    
    KEYSTORE --> PRIVATE_KEY_MEM
    KEYSTORE --> MNEMONIC_MEM
    
    THREATS --> T1
    THREATS --> T2
    THREATS --> T3
    THREATS --> T4
    
    T1 -.Mitigated by.-> ENCRYPTION
    T2 -.Mitigated by.-> HARDWARE_WALLET
    T3 -.Mitigated by.-> TLS
    T4 -.Mitigated by.-> FUTURE_AUTH
    
    style PLAINTEXT fill:#FF4D5A
    style NO_AUTH fill:#FF4D5A
    style FILE_PERMS fill:#FF6B9D
    style ENCRYPTION fill:#34C759
    style HTTPS fill:#34C759
    style TLS fill:#34C759
```


---

## 9. Class Diagram - Core Components

```mermaid
classDiagram
    class AlgorandWallet {
        +str algod_address
        +str algod_token
        +AlgodClient algod_client
        +Path wallet_file
        +str address
        +str private_key
        +str last_error
        +__init__(wallet_file)
        +_load_or_create_wallet()
        +get_balance() float
    }
    
    class NeuroChain {
        +list~Block~ chain
        +list~dict~ pending_tasks
        +float wallet_balance
        +float total_profit
        +int blocks_mined
        +RankingSystem ranking
        +__init__()
        +add_block(data) Block
        +add_company_task(company, model, bounty, benchmark) dict
    }
    
    class Block {
        +int index
        +datetime timestamp
        +str data
        +str previous_hash
        +str hash
        +__init__(index, timestamp, data, prev_hash)
    }
    
    class RankingSystem {
        +int xp
        +int battles_won
        +int battles_lost
        +int valid_blocks
        +str current_tier
        +float avg_accuracy
        +list _accuracy_samples
        +battles_attempted() int
        +win_rate() float
        +_update_avg_accuracy(value)
        +calculate_tier() str
        +record_battle_result(accuracy, rivals, reward) dict
    }
    
    class AITrainer {
        +load_data(task_id) tuple
        +train_model(task_id, stop_flag) generator
    }
    
    class TrainingWorker {
        +dict task
        +bool _stop
        +epoch_done: Signal
        +log_msg: Signal
        +finished_ok: Signal
        +__init__(task)
        +request_stop()
        +run()
    }
    
    class NeuroChainApp {
        +TrainingWorker worker
        +str current_view
        +dict sidebar_buttons
        +QStackedWidget pages
        +dict page_map
        +__init__()
        +_build_page_dashboard() QWidget
        +_build_page_training() QWidget
        +_start_mining()
        +_stop_mining()
        +_on_epoch(epoch, loss, acc)
        +_on_done(task, accuracy, rivals)
    }
    
    class OpportunityShellWindow {
        +bool _allow_close
        +DaemonClient daemon
        +QStackedWidget stack
        +BootScreen boot
        +LockScreen lock
        +DesktopScreen desktop
        +__init__()
        +_show_lock()
        +_show_desktop()
        +_power_off()
    }
    
    NeuroChain "1" *-- "many" Block
    NeuroChain "1" *-- "1" RankingSystem
    NeuroChainApp "1" --> "1" NeuroChain
    NeuroChainApp "1" --> "1" AITrainer
    NeuroChainApp "1" o-- "0..1" TrainingWorker
    TrainingWorker "1" --> "1" AITrainer
    OpportunityShellWindow "1" --> "1" AlgorandWallet
```


---

## 10. Task Marketplace Flow

```mermaid
graph LR
    subgraph "Task Sources"
        CORE[Core Tasks<br/>Neuro Foundation]
        COMPANY[Company Tasks<br/>External Sponsors]
    end
    
    subgraph "Task Registry"
        TASK_LIST[Pending Tasks List]
        
        subgraph "Task Properties"
            ID[Task ID]
            NAME[Task Name]
            BOUNTY[Bounty Amount<br/>ALGO]
            DATASET[Dataset ID]
            SPONSOR[Sponsor Name]
            STATUS[Status<br/>Hot/Live/Listed]
        end
    end
    
    subgraph "User Interface"
        MARKETPLACE[Task Marketplace<br/>Table View]
        
        subgraph "Task Display"
            COL_NAME[Name Column]
            COL_SPONSOR[Sponsor Column]
            COL_IMPACT[Impact Column]
            COL_BOUNTY[Bounty Column]
            COL_DYNAMIC[24h % Column]
            COL_SIGNAL[Signal Chart]
            COL_STATUS[Status Column]
        end
        
        ACTIONS[User Actions]
        SELECT[Select Task]
        START[Start Training]
    end
    
    subgraph "Training Execution"
        WORKER[Training Worker]
        COMPETE[Competition<br/>vs Rivals]
        RESULTS[Results & Payout]
    end
    
    CORE --> TASK_LIST
    COMPANY --> TASK_LIST
    
    TASK_LIST --> ID
    TASK_LIST --> NAME
    TASK_LIST --> BOUNTY
    TASK_LIST --> DATASET
    TASK_LIST --> SPONSOR
    TASK_LIST --> STATUS
    
    ID --> MARKETPLACE
    NAME --> COL_NAME
    SPONSOR --> COL_SPONSOR
    BOUNTY --> COL_BOUNTY
    STATUS --> COL_STATUS
    
    MARKETPLACE --> ACTIONS
    ACTIONS --> SELECT
    SELECT --> START
    
    START --> WORKER
    WORKER --> COMPETE
    COMPETE --> RESULTS
    
    style CORE fill:#6C63FF
    style COMPANY fill:#FF6B9D
    style BOUNTY fill:#34C759
    style RESULTS fill:#00F5FF
```

---

## 11. Reward Distribution Model

```mermaid
graph TB
    START[Training Complete]
    
    START --> SUBMIT[Submit Accuracy Score]
    SUBMIT --> RIVALS[Generate Rival Scores<br/>6-10 competitors]
    
    RIVALS --> RANK[Calculate Rank Position]
    
    RANK --> CHECK{Rank Position?}
    
    CHECK -->|Rank 1| WIN[Winner Path]
    CHECK -->|Rank 2| BREAK[Breakeven Path]
    CHECK -->|Rank 3+| LOSS[Loss Path]
    
    WIN --> WIN_REWARD[Payout: 90% of Bounty]
    WIN --> WIN_XP[XP: +150]
    WIN --> WIN_BLOCK[Mine Block: +1]
    WIN --> WIN_BATTLES[Battles Won: +1]
    
    BREAK --> BREAK_REWARD[Payout: 10% of Bounty]
    BREAK --> BREAK_XP[XP: +25]
    BREAK --> BREAK_BATTLES[Battles Lost: +1]
    
    LOSS --> LOSS_REWARD[Payout: -0.05 ALGO]
    LOSS --> LOSS_XP[XP: +10]
    LOSS --> LOSS_BATTLES[Battles Lost: +1]
    
    WIN_REWARD --> UPDATE_WALLET[Update Wallet Balance]
    BREAK_REWARD --> UPDATE_WALLET
    LOSS_REWARD --> UPDATE_WALLET
    
    WIN_XP --> UPDATE_RANK[Update Ranking Stats]
    BREAK_XP --> UPDATE_RANK
    LOSS_XP --> UPDATE_RANK
    
    WIN_BLOCK --> UPDATE_RANK
    WIN_BATTLES --> UPDATE_RANK
    BREAK_BATTLES --> UPDATE_RANK
    LOSS_BATTLES --> UPDATE_RANK
    
    UPDATE_WALLET --> CALC_TIER[Calculate Tier]
    UPDATE_RANK --> CALC_TIER
    
    CALC_TIER --> TIER_CHECK{Tier Requirements?}
    
    TIER_CHECK -->|100 blocks + 95% acc| ORACLE[Oracle Tier]
    TIER_CHECK -->|100 blocks + 90% acc| ARCHITECT[Architect Tier]
    TIER_CHECK -->|10 blocks + 90% acc| TRAINER[Trainer Tier]
    TIER_CHECK -->|Default| PERCEPTRON[Perceptron Tier]
    
    ORACLE --> PUBLISH[Publish Wallet State]
    ARCHITECT --> PUBLISH
    TRAINER --> PUBLISH
    PERCEPTRON --> PUBLISH
    
    PUBLISH --> UI[Update UI Display]
    UI --> END[Complete]
    
    style WIN fill:#34C759
    style BREAK fill:#F0B90B
    style LOSS fill:#FF4D5A
    style ORACLE fill:#6C63FF
```


---

## 12. Hardware Monitoring Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        UI[User Interface]
        STATS_CARD[Node Stats Card]
        METRICS[Performance Metrics]
    end
    
    subgraph "Monitoring Layer"
        HW_MONITOR[Hardware Monitor]
        TIMER[QTimer<br/>2 second interval]
    end
    
    subgraph "Data Collection"
        NVIDIA_SMI[nvidia-smi Command]
        
        subgraph "GPU Metrics"
            TEMP[Temperature °C]
            FAN[Fan Speed %]
            VRAM_USED[VRAM Used MB]
            VRAM_TOTAL[VRAM Total MB]
            GPU_UTIL[GPU Utilization %]
        end
        
        FALLBACK[Fallback Values<br/>N/A if unavailable]
    end
    
    subgraph "Rust Daemon (Future)"
        DAEMON[Hardware Daemon]
        TELEMETRY[Telemetry API]
        
        subgraph "Advanced Metrics"
            CPU_LOAD[CPU Load %]
            CPU_TEMP[CPU Temperature]
            NET_LATENCY[Network Latency]
            POWER[Power Consumption]
        end
    end
    
    subgraph "Display Layer"
        TEMP_LABEL[Temperature Display]
        FAN_LABEL[Fan Speed Display]
        VRAM_LABEL[VRAM Display]
        UTIL_BAR[GPU Utilization Bar]
    end
    
    UI --> STATS_CARD
    STATS_CARD --> METRICS
    
    TIMER --> HW_MONITOR
    HW_MONITOR --> NVIDIA_SMI
    
    NVIDIA_SMI --> TEMP
    NVIDIA_SMI --> FAN
    NVIDIA_SMI --> VRAM_USED
    NVIDIA_SMI --> VRAM_TOTAL
    NVIDIA_SMI --> GPU_UTIL
    
    NVIDIA_SMI -.Error.-> FALLBACK
    
    TEMP --> TEMP_LABEL
    FAN --> FAN_LABEL
    VRAM_USED --> VRAM_LABEL
    VRAM_TOTAL --> VRAM_LABEL
    GPU_UTIL --> UTIL_BAR
    
    FALLBACK --> TEMP_LABEL
    FALLBACK --> FAN_LABEL
    FALLBACK --> VRAM_LABEL
    
    DAEMON -.Future.-> TELEMETRY
    TELEMETRY -.Future.-> CPU_LOAD
    TELEMETRY -.Future.-> CPU_TEMP
    TELEMETRY -.Future.-> NET_LATENCY
    TELEMETRY -.Future.-> POWER
    
    style NVIDIA_SMI fill:#34C759
    style DAEMON fill:#6C63FF
    style FALLBACK fill:#FF6B9D
```

---

## 13. File System Structure

```mermaid
graph TB
    ROOT[Project Root]
    
    subgraph "Source Code"
        DEMO[neurochain_demo.py<br/>2,345 lines]
        
        DIG_OS[dig_os/]
        UI_SHELL[ui_shell/]
        CORE[core/]
        WALLET_PY[wallet.py<br/>Algorand Integration]
        
        RUST[rust_daemon/<br/>Cargo Project]
        AI_WORKER[ai_worker/<br/>Cython Worker]
    end
    
    subgraph "Data Files"
        DATA[data/]
        KEYSTORE_JSON[keystore.json<br/>Wallet Keys]
        
        RUNTIME[runtime/]
        WALLET_STATE[opportunity_wallet_state.json<br/>Balance Sync]
        
        DATASETS[datasets/]
        CANCER[breast-cancer.csv]
        WINE[wine-quality.csv]
        DIGITS[optical+recognition+of+handwritten+digits/]
    end
    
    subgraph "Assets"
        FONTS[fonts/]
        SOURCE_CODE_PRO[SourceCodePro-Variable.ttf]
        
        IMAGES[images/]
        IMAGE_PNG[image.png<br/>Wallet Background]
    end
    
    subgraph "Build Artifacts"
        BUILD[build/]
        DIST[dist/]
        RELEASE[release/]
        INSTALLER[NuroChainSetup.exe]
        PAYLOAD[nurochain_payload.zip]
    end
    
    subgraph "Configuration"
        VENV[.venv/<br/>Virtual Environment]
        SPECS[*.spec<br/>PyInstaller Config]
        GITIGNORE[.gitignore]
    end
    
    ROOT --> DEMO
    ROOT --> DIG_OS
    DIG_OS --> UI_SHELL
    UI_SHELL --> CORE
    CORE --> WALLET_PY
    
    ROOT --> RUST
    ROOT --> AI_WORKER
    
    ROOT --> DATA
    DATA --> KEYSTORE_JSON
    
    ROOT --> RUNTIME
    RUNTIME --> WALLET_STATE
    
    ROOT --> DATASETS
    DATASETS --> CANCER
    DATASETS --> WINE
    DATASETS --> DIGITS
    
    ROOT --> FONTS
    FONTS --> SOURCE_CODE_PRO
    
    ROOT --> IMAGES
    IMAGES --> IMAGE_PNG
    
    ROOT --> BUILD
    ROOT --> DIST
    ROOT --> RELEASE
    RELEASE --> INSTALLER
    RELEASE --> PAYLOAD
    
    ROOT --> VENV
    ROOT --> SPECS
    ROOT --> GITIGNORE
    
    style WALLET_PY fill:#00F5FF
    style KEYSTORE_JSON fill:#FF4D5A
    style WALLET_STATE fill:#FF6B9D
```


---

## 14. Future Smart Contract Architecture

```mermaid
graph TB
    subgraph "User Layer"
        USERS[Multiple Users<br/>Compute Providers]
        COMPANIES[Companies<br/>Task Sponsors]
    end
    
    subgraph "Algorand Blockchain"
        subgraph "Smart Contracts (PyTeal)"
            TASK_CONTRACT[Task Registry Contract]
            ESCROW[Bounty Escrow Contract]
            VERIFY[Verification Contract]
            PAYOUT[Payout Distribution Contract]
        end
        
        subgraph "On-Chain Data"
            TASK_STATE[Task State<br/>Active/Complete]
            RESULTS[Training Results<br/>Accuracy Scores]
            RANKINGS[User Rankings<br/>Reputation]
        end
        
        subgraph "Algorand Features"
            ASA[Algorand Standard Assets<br/>Custom Tokens]
            ATOMIC[Atomic Transfers<br/>Multi-sig]
            STATEFUL[Stateful Apps<br/>Global/Local State]
        end
    end
    
    subgraph "Off-Chain Components"
        IPFS[IPFS<br/>Dataset Storage]
        ORACLE[Oracle Network<br/>Result Verification]
        ZK_PROOF[ZK-SNARK Proofs<br/>Privacy Layer]
    end
    
    subgraph "Client Application"
        WALLET[Wallet Client]
        TRAINER[Training Engine]
        SUBMITTER[Result Submitter]
    end
    
    COMPANIES --> TASK_CONTRACT
    TASK_CONTRACT --> ESCROW
    TASK_CONTRACT --> TASK_STATE
    
    USERS --> WALLET
    WALLET --> TRAINER
    TRAINER --> IPFS
    TRAINER --> ZK_PROOF
    
    TRAINER --> SUBMITTER
    SUBMITTER --> VERIFY
    
    VERIFY --> ORACLE
    ORACLE --> RESULTS
    
    RESULTS --> RANKINGS
    RANKINGS --> PAYOUT
    
    PAYOUT --> ESCROW
    ESCROW --> USERS
    
    TASK_CONTRACT --> ASA
    VERIFY --> ATOMIC
    TASK_STATE --> STATEFUL
    
    style TASK_CONTRACT fill:#6C63FF
    style ESCROW fill:#34C759
    style ZK_PROOF fill:#FF6B9D
    style IPFS fill:#00F5FF
```

---

## 15. Network Communication Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant SDK as py-algorand-sdk
    participant HTTP as HTTPS Client
    participant Node as Algorand Node
    participant Chain as Blockchain
    
    Note over App,Chain: Wallet Creation Flow
    
    App->>SDK: account.generate_account()
    SDK-->>App: (private_key, address)
    
    App->>SDK: mnemonic.from_private_key(private_key)
    SDK-->>App: 25-word mnemonic
    
    App->>App: Save to keystore.json
    
    Note over App,Chain: Balance Query Flow
    
    App->>SDK: algod_client.account_info(address)
    SDK->>HTTP: GET /v2/accounts/{address}
    HTTP->>Node: HTTPS Request
    
    Node->>Chain: Query Account State
    Chain-->>Node: Account Data
    
    Node-->>HTTP: JSON Response
    HTTP-->>SDK: Account Info
    SDK-->>App: {amount: microAlgos, ...}
    
    App->>App: Convert microAlgos to ALGO
    App->>App: Update UI Display
    
    Note over App,Chain: Future Transaction Flow
    
    App->>SDK: transaction.PaymentTxn(...)
    SDK-->>App: Unsigned Transaction
    
    App->>SDK: txn.sign(private_key)
    SDK-->>App: Signed Transaction
    
    App->>SDK: algod_client.send_transaction(signed_txn)
    SDK->>HTTP: POST /v2/transactions
    HTTP->>Node: HTTPS Request
    
    Node->>Chain: Broadcast Transaction
    Chain-->>Node: Transaction ID
    
    Node-->>HTTP: {txId: "..."}
    HTTP-->>SDK: Transaction ID
    SDK-->>App: Transaction ID
    
    App->>App: Wait for Confirmation
    
    loop Every 1 second
        App->>SDK: algod_client.pending_transaction_info(txId)
        SDK->>HTTP: GET /v2/transactions/pending/{txId}
        HTTP->>Node: HTTPS Request
        Node-->>HTTP: Transaction Status
        HTTP-->>SDK: Status
        SDK-->>App: {confirmed-round: N}
    end
    
    App->>App: Transaction Confirmed!
```


---

## 16. Error Handling & Recovery

```mermaid
graph TB
    START[Application Start]
    
    START --> CHECK_SDK{py-algorand-sdk<br/>Available?}
    
    CHECK_SDK -->|Yes| INIT_WALLET[Initialize Wallet]
    CHECK_SDK -->|No| CHECK_VENV{Virtual Env<br/>Exists?}
    
    CHECK_VENV -->|Yes| REEXEC[Re-execute with<br/>venv Python]
    CHECK_VENV -->|No| ERROR_SDK[Show Error:<br/>Install algosdk]
    
    REEXEC --> CHECK_SDK
    ERROR_SDK --> DEGRADED[Run in Degraded Mode<br/>No Blockchain Features]
    
    INIT_WALLET --> LOAD_WALLET{Keystore<br/>Exists?}
    
    LOAD_WALLET -->|Yes| VALIDATE{Valid<br/>Format?}
    LOAD_WALLET -->|No| CREATE_WALLET[Create New Wallet]
    
    VALIDATE -->|Yes| LOAD_KEYS[Load Keys from File]
    VALIDATE -->|No| CREATE_WALLET
    
    CREATE_WALLET --> GENERATE[Generate Account]
    GENERATE --> SAVE_KEYS[Save to Keystore]
    SAVE_KEYS --> READY[Wallet Ready]
    
    LOAD_KEYS --> READY
    
    READY --> QUERY_BALANCE[Query Balance]
    
    QUERY_BALANCE --> NETWORK{Network<br/>Available?}
    
    NETWORK -->|Yes| GET_BALANCE[Get Account Info]
    NETWORK -->|No| RETRY{Retry<br/>Count < 3?}
    
    RETRY -->|Yes| WAIT[Wait 2 seconds]
    RETRY -->|No| NETWORK_ERROR[Show Network Error<br/>Display 0.00 ALGO]
    
    WAIT --> QUERY_BALANCE
    
    GET_BALANCE --> API_RESPONSE{API<br/>Success?}
    
    API_RESPONSE -->|Yes| UPDATE_UI[Update UI with Balance]
    API_RESPONSE -->|No| API_ERROR[Log Error<br/>Display Last Known Balance]
    
    UPDATE_UI --> RUNNING[Application Running]
    API_ERROR --> RUNNING
    NETWORK_ERROR --> RUNNING
    DEGRADED --> RUNNING
    
    RUNNING --> TRAINING{User Starts<br/>Training?}
    
    TRAINING -->|Yes| LOAD_DATASET{Dataset<br/>Available?}
    TRAINING -->|No| RUNNING
    
    LOAD_DATASET -->|Yes| TRAIN[Execute Training]
    LOAD_DATASET -->|No| DATASET_ERROR[Show Error:<br/>Dataset Missing]
    
    DATASET_ERROR --> RUNNING
    
    TRAIN --> TRAIN_ERROR{Training<br/>Error?}
    
    TRAIN_ERROR -->|Yes| LOG_ERROR[Log Error<br/>Show User Message]
    TRAIN_ERROR -->|No| COMPLETE[Training Complete]
    
    LOG_ERROR --> RUNNING
    COMPLETE --> RUNNING
    
    style ERROR_SDK fill:#FF4D5A
    style NETWORK_ERROR fill:#FF4D5A
    style API_ERROR fill:#FF6B9D
    style DATASET_ERROR fill:#FF6B9D
    style DEGRADED fill:#F0B90B
    style READY fill:#34C759
    style COMPLETE fill:#34C759
```

---

## 17. Development vs Production Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_MACHINE[Developer Laptop]
        
        subgraph "Dev Tools"
            VSCODE[VS Code / IDE]
            DEBUGGER[Python Debugger]
            HOT_RELOAD[Hot Reload]
        end
        
        subgraph "Dev Services"
            LOCAL_TESTNET[Local Algorand Node<br/>Optional]
            PUBLIC_TESTNET[Public TestNet<br/>Default]
        end
        
        subgraph "Dev Data"
            DEV_KEYSTORE[Test Keystore<br/>Disposable Keys]
            DEV_DATASETS[Sample Datasets<br/>Small Size]
        end
    end
    
    subgraph "Production Environment"
        USER_MACHINE[User Computer]
        
        subgraph "Prod Application"
            BUNDLED_EXE[Bundled .exe<br/>PyInstaller]
            EMBEDDED_DEPS[Embedded Dependencies<br/>No Python Required]
        end
        
        subgraph "Prod Services"
            MAINNET[Algorand MainNet<br/>Production]
            BACKUP_NODE[Backup Node<br/>Failover]
        end
        
        subgraph "Prod Data"
            PROD_KEYSTORE[User Keystore<br/>Real Keys]
            PROD_DATASETS[Full Datasets<br/>Production Size]
            ENCRYPTED[Encrypted Storage<br/>Future]
        end
    end
    
    subgraph "CI/CD Pipeline"
        GITHUB[GitHub Repository]
        ACTIONS[GitHub Actions]
        
        subgraph "Build Steps"
            LINT[Linting<br/>flake8/black]
            TEST[Unit Tests<br/>pytest]
            BUILD[PyInstaller Build]
            SIGN[Code Signing<br/>Future]
        end
        
        RELEASE[Release Artifacts]
    end
    
    DEV_MACHINE --> VSCODE
    VSCODE --> DEBUGGER
    VSCODE --> HOT_RELOAD
    
    DEV_MACHINE --> LOCAL_TESTNET
    DEV_MACHINE --> PUBLIC_TESTNET
    DEV_MACHINE --> DEV_KEYSTORE
    DEV_MACHINE --> DEV_DATASETS
    
    USER_MACHINE --> BUNDLED_EXE
    BUNDLED_EXE --> EMBEDDED_DEPS
    
    USER_MACHINE --> MAINNET
    USER_MACHINE --> BACKUP_NODE
    USER_MACHINE --> PROD_KEYSTORE
    USER_MACHINE --> PROD_DATASETS
    PROD_KEYSTORE -.Future.-> ENCRYPTED
    
    DEV_MACHINE --> GITHUB
    GITHUB --> ACTIONS
    
    ACTIONS --> LINT
    ACTIONS --> TEST
    ACTIONS --> BUILD
    ACTIONS --> SIGN
    
    BUILD --> RELEASE
    RELEASE --> USER_MACHINE
    
    style DEV_MACHINE fill:#6C63FF
    style USER_MACHINE fill:#34C759
    style MAINNET fill:#FF4D5A
    style PUBLIC_TESTNET fill:#00F5FF
```


---

## 18. Technology Stack Overview

```mermaid
mindmap
  root((Opportunity OS))
    Frontend
      UI Framework
        PySide6 Qt6
        PyQt6 Qt6
      Graphics
        PyQtGraph Charts
        QtAwesome Icons
      Styling
        QSS Stylesheets
        Nebula Glass Design
    Backend
      Language
        Python 3.10+
        Rust Daemon
        Cython Worker
      ML/AI
        scikit-learn
        NumPy
        pandas
      Blockchain
        py-algorand-sdk
        Algorand TestNet
        Future: PyTeal
    Data
      Storage
        JSON Files
        CSV Datasets
      Formats
        Keystore JSON
        Wallet State JSON
        Training Data CSV
    Infrastructure
      Build
        PyInstaller
        Cargo Rust
        setuptools
      Deployment
        Windows Installer
        Linux Package
        macOS Bundle
      Monitoring
        nvidia-smi
        Hardware Telemetry
        Performance Metrics
    Security
      Cryptography
        Algorand Keys
        Mnemonic Phrases
        Future: Encryption
      Network
        HTTPS Only
        TLS 1.2+
        Certificate Validation
```

---

## Summary

This comprehensive architecture documentation covers:

1. **System Overview** - High-level component interaction
2. **Component Architecture** - Detailed module breakdown
3. **Data Flow** - Sequence of operations
4. **Blockchain Integration** - Algorand SDK usage
5. **Training Workflow** - State machine for ML training
6. **UI Structure** - Component hierarchy
7. **Deployment** - Build and distribution pipeline
8. **Security** - Threat model and mitigations
9. **Class Diagram** - Object-oriented design
10. **Task Marketplace** - Task flow and selection
11. **Reward Distribution** - Payout calculation logic
12. **Hardware Monitoring** - GPU/CPU telemetry
13. **File System** - Project structure
14. **Future Smart Contracts** - Planned blockchain features
15. **Network Communication** - API interaction flow
16. **Error Handling** - Recovery strategies
17. **Dev vs Prod** - Environment differences
18. **Technology Stack** - Complete tech overview

---

## How to Use These Diagrams

### Viewing in GitHub
These Mermaid diagrams render automatically in GitHub markdown files.

### Viewing Locally
Use a Mermaid-compatible markdown viewer:
- VS Code with Mermaid extension
- Obsidian
- Typora
- Online: https://mermaid.live/

### Exporting
Convert to images using:
```bash
# Using mermaid-cli
mmdc -i architecture_diagrams.md -o architecture_diagrams.pdf

# Or use online tools
# https://mermaid.live/ -> Export as PNG/SVG
```

---

**Document Version**: 1.0  
**Last Updated**: February 20, 2026  
**Status**: Complete
