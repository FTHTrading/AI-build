# EXECUTIVE DECISION & EXECUTION REGISTRY
**Entity**: Unykorn LLC | **Executive Authority**: Kevan Burns (Founder, Owner & CEO)

```dataviewjs
// 1. Fetch all daily transaction files
const dailyLogs = dv.pages('"04_EPISODIC_MEMORY/DAILY_TRANSACTIONS"')
  .sort(p => p.file.name, 'desc');

// 2. Parse execution run blocks across Markdown files
let executionRuns = [];

for (let page of dailyLogs) {
    const fileContent = await app.vault.read(app.vault.getAbstractFileByPath(page.file.path));
    const rawSections = fileContent.split(/^### /m).slice(1);

    for (let section of rawSections) {
        const lines = section.split("\n");
        const headerLine = lines[0].trim();
        
        // Extract timestamp and title
        const timeMatch = headerLine.match(/^\[(.*?)\]\s*-\s*(.*)$/);
        const timestamp = timeMatch ? timeMatch[1] : "N/A";
        const title = timeMatch ? timeMatch[2] : headerLine;

        // Extract metadata fields via regex
        const sessionMatch = section.match(/- \*\*Session ID\*\*:\s*`?(.*?)`?$/m);
        const moduleMatch = section.match(/- \*\*Module Context\*\*:\s*\[\[(.*?)\]\]/m);
        const statusMatch = section.match(/- \*\*Status\*\*:\s*`?(.*?)`?$/m);
        const artifactMatch = section.match(/- \*\*Artifact Generated\*\*:\s*`?(.*?)`?$/m);
        const notesMatch = section.match(/>\s*(.*)$/m);

        executionRuns.push({
            date: page.file.name,
            timestamp: timestamp,
            title: title,
            session: sessionMatch ? sessionMatch[1].trim() : "N/A",
            module: moduleMatch ? moduleMatch[1].trim() : "UNASSIGNED",
            status: statusMatch ? statusMatch[1].trim() : "UNKNOWN",
            artifact: artifactMatch ? artifactMatch[1].trim() : "N/A",
            summary: notesMatch ? notesMatch[1].trim() : "No summary provided.",
            link: page.file.link
        });
    }
}

// 3. Render Executive Metrics Summary
const totalRuns = executionRuns.length;
const successfulRuns = executionRuns.filter(r => r.status.toUpperCase() === "SUCCESS" || r.status.toUpperCase() === "COMPLETED").length;
const activeModules = [...new Set(executionRuns.map(r => r.module))].length;

dv.paragraph(`
> [!info] **Unykorn Runtime Metrics**
> **Total Logged Runs**: \`${totalRuns}\` | **Success Rate**: \`${totalRuns > 0 ? ((successfulRuns / totalRuns) * 100).toFixed(1) : 0}%\` | **Active Neural Modules**: \`${activeModules}\`
`);

// 4. Render Master Aggregated Table
dv.table(
    ["Date", "Time", "Execution Run", "Module Context", "Status", "Artifact", "Log File"],
    executionRuns.map(run => [
        run.date,
        run.timestamp,
        `**${run.title}**<br><small style="color: gray;">${run.summary}</small>`,
        `[[${run.module}]]`,
        run.status.toUpperCase() === "SUCCESS" || run.status.toUpperCase() === "COMPLETED" 
            ? `<span style="color: #4ade80; font-weight: bold;">● ${run.status}</span>`
            : `<span style="color: #f87171; font-weight: bold;">▲ ${run.status}</span>`,
        `\`${run.artifact}\``,
        run.link
    ])
);
```
