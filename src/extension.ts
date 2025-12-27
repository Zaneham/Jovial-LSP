import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    // Get configuration
    const config = vscode.workspace.getConfiguration('jovial');
    const pythonPath = config.get<string>('pythonPath', 'python');
    let serverPath = config.get<string>('serverPath', '');

    // Use bundled server if not specified
    if (!serverPath) {
        serverPath = context.asAbsolutePath(
            path.join('jovial_lsp_server.py')
        );
    }

    // Server options - run Python LSP server
    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: [serverPath],
        transport: TransportKind.stdio
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'jovial' }
        ],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{jov,j73,cpl,jovial}')
        }
    };

    // Create and start the client
    client = new LanguageClient(
        'jovialLSP',
        'JOVIAL J73 Language Server',
        serverOptions,
        clientOptions
    );

    // Start the client
    client.start();

    // Register status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(file-code) JOVIAL J73';
    statusBarItem.tooltip = 'JOVIAL J73 Language Support (MIL-STD-1589C)';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Show welcome message
    vscode.window.showInformationMessage(
        'JOVIAL J73 Language Server activated - Supporting F-15, B-52, AWACS, and other critical systems'
    );
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
