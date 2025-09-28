use clap::Parser;
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::{env, io::Write, collections::HashMap};
use dialoguer::{Select, theme::ColorfulTheme};
use arboard::Clipboard;
use webbrowser;
use console::{style, Term, Emoji, Key};
use textwrap;

const ADS_API_BASE_URL: &str = "https://api.adsabs.harvard.edu/v1";

// Emoji constants for better terminal display
static TELESCOPE: Emoji<'_, '_> = Emoji("🔭 ", "");
static PAPER: Emoji<'_, '_> = Emoji("📄 ", "");
static AUTHOR: Emoji<'_, '_> = Emoji("👤 ", "");
static CALENDAR: Emoji<'_, '_> = Emoji("📅 ", "");
static JOURNAL: Emoji<'_, '_> = Emoji("📚 ", "");
static CITATION: Emoji<'_, '_> = Emoji("📊 ", "");
static ABSTRACT: Emoji<'_, '_> = Emoji("📝 ", "");
static SEARCH: Emoji<'_, '_> = Emoji("🔍 ", "");
static ROCKET: Emoji<'_, '_> = Emoji("🚀 ", "");
static SPARKLES: Emoji<'_, '_> = Emoji("✨ ", "");
static CLIPBOARD: Emoji<'_, '_> = Emoji("📋 ", "");
static BROWSER: Emoji<'_, '_> = Emoji("🌐 ", "");
static BACK: Emoji<'_, '_> = Emoji("← ", "<- ");
static QUIT: Emoji<'_, '_> = Emoji("❌ ", "X ");
static SUCCESS: Emoji<'_, '_> = Emoji("✅ ", "[OK] ");
static ERROR: Emoji<'_, '_> = Emoji("❌ ", "[ERROR] ");
static LOADING: Emoji<'_, '_> = Emoji("⏳ ", "...");
static PAGE: Emoji<'_, '_> = Emoji("📖 ", "Page ");
static MAGNIFY: Emoji<'_, '_> = Emoji("🔍 ", "Search ");
static REFERENCES: Emoji<'_, '_> = Emoji("📚 ", "Refs ");
static CITATIONS: Emoji<'_, '_> = Emoji("🔗 ", "Cites ");
static SIMILAR: Emoji<'_, '_> = Emoji("🔄 ", "Similar ");

#[derive(Parser)]
#[command(name = "ads")]
#[command(about = "A CLI tool for querying NASA/ADS API")]
struct Cli {
    /// Search query (Solr syntax) - can be multiple words
    query_parts: Vec<String>,

    /// Number of results per page (default: 10)
    #[arg(short, long, default_value = "10")]
    rows: u32,

    /// Fields to return (comma-separated)
    #[arg(short, long, default_value = "bibcode,title,first_author,year")]
    fields: String,

    /// Disable interactive mode (show plain list instead)
    #[arg(long)]
    no_interactive: bool,
}

#[derive(Deserialize, Debug)]
struct AdsResponse {
    response: AdsResponseBody,
}

#[derive(Deserialize, Debug)]
struct AdsResponseBody {
    docs: Vec<serde_json::Value>,
    #[serde(rename = "numFound")]
    num_found: u32,
    #[allow(dead_code)]
    start: u32,
}

#[derive(Debug)]
enum PaperAction {
    BackToList,
    CopyBibtex,
    OpenInBrowser,
    ShowReferences,
    ShowCitations,
    ShowSimilar,
    Quit,
}

#[derive(Debug)]
enum PageAction {
    SelectPaper(usize),
    NextPage,
    PrevPage,
    SearchMode,
    Quit,
}

#[derive(Serialize)]
struct SearchParams {
    q: String,
    fl: String,
    rows: u32,
    start: u32,
}

async fn fetch_bibtex(bibcode: &str) -> Result<String> {
    let token = env::var("ADS_API_TOKEN")
        .context("ADS_API_TOKEN environment variable not set")?;

    let client = reqwest::Client::new();
    let url = format!("{}/export/bibtex", ADS_API_BASE_URL);

    #[derive(Serialize)]
    struct BibtexRequest {
        bibcode: Vec<String>,
    }

    let request_body = BibtexRequest {
        bibcode: vec![bibcode.to_string()],
    };

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("User-Agent", "ads-rust-cli/0.1.0")
        .header("Content-Type", "application/json")
        .json(&request_body)
        .send()
        .await
        .context("Failed to send bibtex request to ADS API")?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        anyhow::bail!("ADS bibtex request failed with status {}: {}", status, text);
    }

    let bibtex_data = response
        .text()
        .await
        .context("Failed to get bibtex text from ADS API")?;

    Ok(bibtex_data)
}

async fn search_ads(query: &str, fields: &str, rows: u32, start: u32) -> Result<AdsResponse> {
    let token = env::var("ADS_API_TOKEN")
        .context("ADS_API_TOKEN environment variable not set. Get your token from https://ui.adsabs.harvard.edu/user/settings/token")?;

    let client = reqwest::Client::new();
    let url = format!("{}/search/query", ADS_API_BASE_URL);

    let params = SearchParams {
        q: query.to_string(),
        fl: fields.to_string(),
        rows,
        start,
    };

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("User-Agent", "ads-rust-cli/0.1.0")
        .query(&params)
        .send()
        .await
        .context("Failed to send request to ADS API")?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        anyhow::bail!("ADS API request failed with status {}: {}", status, text);
    }

    let ads_response: AdsResponse = response
        .json()
        .await
        .context("Failed to parse JSON response from ADS API")?;

    Ok(ads_response)
}

async fn get_paper_references(bibcode: &str, rows: u32) -> Result<AdsResponse> {
    let token = env::var("ADS_API_TOKEN")
        .context("ADS_API_TOKEN environment variable not set")?;

    let client = reqwest::Client::new();
    let url = format!("{}/search/query", ADS_API_BASE_URL);

    // Query for papers referenced by this paper
    let query = format!("references(bibcode:{})", bibcode);

    let params = SearchParams {
        q: query,
        fl: "bibcode,title,first_author,year,author,pub,citation_count,abstract".to_string(),
        rows,
        start: 0,
    };

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("User-Agent", "ads-rust-cli/0.1.0")
        .query(&params)
        .send()
        .await
        .context("Failed to send references request to ADS API")?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        anyhow::bail!("ADS references request failed with status {}: {}", status, text);
    }

    let ads_response: AdsResponse = response
        .json()
        .await
        .context("Failed to parse JSON response from ADS API")?;

    Ok(ads_response)
}

async fn get_paper_citations(bibcode: &str, rows: u32) -> Result<AdsResponse> {
    let token = env::var("ADS_API_TOKEN")
        .context("ADS_API_TOKEN environment variable not set")?;

    let client = reqwest::Client::new();
    let url = format!("{}/search/query", ADS_API_BASE_URL);

    // Query for papers that cite this paper
    let query = format!("citations(bibcode:{})", bibcode);

    let params = SearchParams {
        q: query,
        fl: "bibcode,title,first_author,year,author,pub,citation_count,abstract".to_string(),
        rows,
        start: 0,
    };

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("User-Agent", "ads-rust-cli/0.1.0")
        .query(&params)
        .send()
        .await
        .context("Failed to send citations request to ADS API")?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        anyhow::bail!("ADS citations request failed with status {}: {}", status, text);
    }

    let ads_response: AdsResponse = response
        .json()
        .await
        .context("Failed to parse JSON response from ADS API")?;

    Ok(ads_response)
}

async fn get_similar_papers(bibcode: &str, rows: u32) -> Result<AdsResponse> {
    let token = env::var("ADS_API_TOKEN")
        .context("ADS_API_TOKEN environment variable not set")?;

    let client = reqwest::Client::new();
    let url = format!("{}/search/query", ADS_API_BASE_URL);

    // Query for papers similar to this paper using the similar() function
    let query = format!("similar(bibcode:{})", bibcode);

    let params = SearchParams {
        q: query,
        fl: "bibcode,title,first_author,year,author,pub,citation_count,abstract".to_string(),
        rows,
        start: 0,
    };

    let response = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("User-Agent", "ads-rust-cli/0.1.0")
        .query(&params)
        .send()
        .await
        .context("Failed to send similar papers request to ADS API")?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        anyhow::bail!("ADS similar papers request failed with status {}: {}", status, text);
    }

    let ads_response: AdsResponse = response
        .json()
        .await
        .context("Failed to parse JSON response from ADS API")?;

    Ok(ads_response)
}

fn format_paper(doc: &serde_json::Value) -> String {
    let bibcode = doc.get("bibcode")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let title = doc.get("title")
        .and_then(|v| v.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let first_author = doc.get("first_author")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let year = doc.get("year")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    format!("{} | {} | {} ({})", bibcode, first_author, title, year)
}

fn format_paper_short(doc: &serde_json::Value) -> String {
    let title = doc.get("title")
        .and_then(|v| v.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let first_author = doc.get("first_author")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let year = doc.get("year")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let citation_count = doc.get("citation_count")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);

    // Truncate title if too long for better display in selection
    let truncated_title = if title.len() > 55 {
        format!("{}...", &title[..52])
    } else {
        title.to_string()
    };

    // Color coding based on citation count
    let author_styled = if citation_count > 100 {
        style(first_author).bold().yellow()
    } else if citation_count > 50 {
        style(first_author).bold().cyan()
    } else {
        style(first_author).white()
    };

    let year_styled = style(year).dim();
    let citations_styled = if citation_count > 0 {
        style(format!("({}🔗)", citation_count)).dim().green()
    } else {
        style(String::new()).dim()
    };

    format!("{} {} - {} {}",
        author_styled,
        year_styled,
        style(truncated_title).white(),
        citations_styled
    )
}

fn display_paper_details(doc: &serde_json::Value) {
    let term = Term::stdout();
    let width = term.size().1 as usize;
    let separator = "─".repeat(width.min(80));

    println!("\n{}", style(format!("{}Paper Details", PAPER)).bold().blue());
    println!("{}", style(&separator).dim());

    if let Some(title) = doc.get("title")
        .and_then(|v| v.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str()) {
        println!("\n{}{}",
            style("Title: ").bold().cyan(),
            style(title).bold().white()
        );
    }

    if let Some(first_author) = doc.get("first_author").and_then(|v| v.as_str()) {
        print!("\n{}{}",
            style(format!("{}First Author: ", AUTHOR)).bold().cyan(),
            style(first_author).yellow()
        );
    }

    if let Some(year) = doc.get("year").and_then(|v| v.as_str()) {
        print!("  {}{}",
            style(format!("{}Year: ", CALENDAR)).bold().cyan(),
            style(year).green()
        );
    }

    if let Some(citation_count) = doc.get("citation_count").and_then(|v| v.as_u64()) {
        println!("  {}{}",
            style(format!("{}Citations: ", CITATION)).bold().cyan(),
            style(citation_count.to_string()).magenta()
        );
    } else {
        println!();
    }

    if let Some(pub_name) = doc.get("pub").and_then(|v| v.as_str()) {
        println!("\n{}{}",
            style(format!("{}Publication: ", JOURNAL)).bold().cyan(),
            style(pub_name).italic()
        );
    }

    if let Some(bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
        println!("\n{}{}",
            style("Bibcode: ").bold().cyan(),
            style(bibcode).dim()
        );
    }

    if let Some(authors) = doc.get("author").and_then(|v| v.as_array()) {
        let author_names: Vec<String> = authors.iter()
            .filter_map(|v| v.as_str())
            .take(10) // Limit to first 10 authors
            .map(|s| s.to_string())
            .collect();
        if !author_names.is_empty() {
            let authors_text = if authors.len() > 10 {
                format!("{} (+{} more)", author_names.join(", "), authors.len() - 10)
            } else {
                author_names.join(", ")
            };
            println!("\n{}All Authors: {}",
                style(format!("{}Authors: ", AUTHOR)).bold().cyan(),
                style(authors_text).dim()
            );
        }
    }

    if let Some(abstract_text) = doc.get("abstract").and_then(|v| v.as_str()) {
        println!("\n{}",
            style(format!("{}Abstract:", ABSTRACT)).bold().cyan()
        );

        // Word wrap the abstract
        let wrapped_abstract = textwrap::fill(abstract_text, width.min(80));
        for line in wrapped_abstract.lines() {
            println!("  {}", style(line).italic().dim());
        }
    }

    println!("\n{}\n", style(&separator).dim());
}

async fn handle_paper_actions(doc: &serde_json::Value) -> Result<PaperAction> {
    let actions = vec![
        format!("{}Back to list", BACK),
        format!("{}Copy BibTeX to clipboard", CLIPBOARD),
        format!("{}Open in browser", BROWSER),
        format!("{}Show references", REFERENCES),
        format!("{}Show citations", CITATIONS),
        format!("{}Show similar papers", SIMILAR),
        format!("{}Quit", QUIT),
    ];

    let selection = Select::with_theme(&ColorfulTheme::default())
        .with_prompt(&format!("{}What would you like to do?", SPARKLES))
        .default(0)
        .items(&actions)
        .interact()?;

    match selection {
        0 => Ok(PaperAction::BackToList),
        1 => {
            // Copy BibTeX to clipboard
            if let Some(bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                print!("{}Fetching BibTeX... ", LOADING);
                Write::flush(&mut std::io::stdout()).unwrap();

                match fetch_bibtex(bibcode).await {
                    Ok(bibtex) => {
                        match Clipboard::new() {
                            Ok(mut clipboard) => {
                                match clipboard.set_text(bibtex.trim()) {
                                    Ok(_) => println!("{}BibTeX copied to clipboard!",
                                        style(format!("{}", SUCCESS)).green()),
                                    Err(e) => println!("{}Failed to copy to clipboard: {}",
                                        style(format!("{}", ERROR)).red(), e),
                                }
                            }
                            Err(e) => println!("{}Failed to access clipboard: {}",
                                style(format!("{}", ERROR)).red(), e),
                        }
                    }
                    Err(e) => println!("{}Failed to fetch BibTeX: {}",
                        style(format!("{}", ERROR)).red(), e),
                }

                println!("\n{}Press Enter to continue...", style("").dim());
                let mut input = String::new();
                std::io::stdin().read_line(&mut input).ok();
            } else {
                println!("{}No bibcode available for this paper",
                    style(format!("{}", ERROR)).red());
            }
            Ok(PaperAction::CopyBibtex)
        }
        2 => {
            // Open in browser
            if let Some(bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                let url = format!("https://ui.adsabs.harvard.edu/abs/{}", bibcode);
                match webbrowser::open(&url) {
                    Ok(_) => println!("{}Opening paper in browser...",
                        style(format!("{}", BROWSER)).green()),
                    Err(e) => println!("{}Failed to open browser: {}",
                        style(format!("{}", ERROR)).red(), e),
                }
            } else {
                println!("{}No bibcode available for this paper",
                    style(format!("{}", ERROR)).red());
            }
            Ok(PaperAction::OpenInBrowser)
        }
        3 => {
            // Show references
            if let Some(_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                println!("{}Finding papers referenced by this paper...",
                    style(format!("{}", REFERENCES)).blue());
                Ok(PaperAction::ShowReferences)
            } else {
                println!("{}No bibcode available for this paper",
                    style(format!("{}", ERROR)).red());
                Ok(PaperAction::BackToList)
            }
        }
        4 => {
            // Show citations
            if let Some(_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                println!("{}Finding papers that cite this paper...",
                    style(format!("{}", CITATIONS)).blue());
                Ok(PaperAction::ShowCitations)
            } else {
                println!("{}No bibcode available for this paper",
                    style(format!("{}", ERROR)).red());
                Ok(PaperAction::BackToList)
            }
        }
        5 => {
            // Show similar papers
            if let Some(_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                println!("{}Finding papers similar to this one...",
                    style(format!("{}", SIMILAR)).blue());
                Ok(PaperAction::ShowSimilar)
            } else {
                println!("{}No bibcode available for this paper",
                    style(format!("{}", ERROR)).red());
                Ok(PaperAction::BackToList)
            }
        }
        6 => Ok(PaperAction::Quit),
        _ => Ok(PaperAction::BackToList),
    }
}

fn show_paginated_papers(docs: &[serde_json::Value], current_page: u32, total_results: u32, results_per_page: u32) -> Result<PageAction> {
    let total_pages = (total_results + results_per_page - 1) / results_per_page;
    let term = Term::stdout();
    let mut selected_index = 0usize; // Cursor position

    let items: Vec<String> = docs.iter()
        .map(format_paper_short)
        .collect();

    if items.is_empty() {
        println!("\n{}No papers on this page", style("📭").yellow());
        println!("\nPress any key to continue...");
        term.read_key()?;
        return Ok(PageAction::Quit);
    }

    loop {
        // Clear screen and show header
        term.clear_screen()?;

        println!("{}{} {}",
            style(format!("{}", TELESCOPE)).blue(),
            style("ADS Paper Browser").bold().blue(),
            style(format!("- Page {} of {}", current_page + 1, total_pages)).dim()
        );

        println!("{}{}",
            style(format!("{}", SPARKLES)).blue(),
            style("Navigate: ← → pages, ↑ ↓ select, Enter view, / search, q quit").dim()
        );

        // Show pagination info
        println!("\n{}Page {} of {} ({} total results)",
            style(format!("{}", PAGE)).cyan(),
            style((current_page + 1).to_string()).bold().yellow(),
            style(total_pages.to_string()).bold(),
            style(total_results.to_string()).dim()
        );

        // Show papers with cursor
        println!();
        for (i, item) in items.iter().enumerate() {
            if i == selected_index {
                // Highlighted/selected item
                println!("{}▶ {}",
                    style(format!("{:2}", i + 1)).bold().yellow(),
                    style(item).bold().white()
                );
            } else {
                // Regular item
                println!("{}  {}",
                    style(format!("{:2}", i + 1)).dim(),
                    style(item).dim()
                );
            }
        }

        // Show navigation instructions
        println!();
        let mut nav_parts = Vec::new();
        if current_page > 0 {
            nav_parts.push(format!("{}← Prev", style("").cyan()));
        }
        if (current_page + 1) * results_per_page < total_results {
            nav_parts.push(format!("{}→ Next", style("").cyan()));
        }
        if !nav_parts.is_empty() {
            println!("{}", style(nav_parts.join("  |  ")).dim());
        }

        println!("\n{}Controls: ↑↓ select, ← → pages, Enter to view paper, q to quit",
            style("⌨️  ").blue()
        );

        // Custom key handling with cursor
        match term.read_key()? {
            Key::ArrowUp => {
                if selected_index > 0 {
                    selected_index -= 1;
                }
            }
            Key::ArrowDown => {
                if selected_index < items.len() - 1 {
                    selected_index += 1;
                }
            }
            Key::ArrowLeft => {
                if current_page > 0 {
                    return Ok(PageAction::PrevPage);
                }
            }
            Key::ArrowRight => {
                if (current_page + 1) * results_per_page < total_results {
                    return Ok(PageAction::NextPage);
                }
            }
            Key::Enter => {
                return Ok(PageAction::SelectPaper(selected_index));
            }
            Key::Char('q') | Key::Char('Q') | Key::Escape => {
                return Ok(PageAction::Quit);
            }
            Key::Char('/') => {
                return Ok(PageAction::SearchMode);
            }
            Key::Char(c) if c.is_ascii_digit() => {
                let num = c.to_digit(10).unwrap() as usize;
                if num >= 1 && num <= items.len() {
                    selected_index = num - 1;
                }
            }
            _ => {
                // Ignore other keys
            }
        }
    }
}

fn paper_matches_search(doc: &serde_json::Value, search_term: &str) -> bool {
    if search_term.is_empty() {
        return true;
    }

    let search_lower = search_term.to_lowercase();

    // Search in title
    if let Some(title) = doc.get("title")
        .and_then(|v| v.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str()) {
        if title.to_lowercase().contains(&search_lower) {
            return true;
        }
    }

    // Search in author
    if let Some(first_author) = doc.get("first_author").and_then(|v| v.as_str()) {
        if first_author.to_lowercase().contains(&search_lower) {
            return true;
        }
    }

    // Search in all authors
    if let Some(authors) = doc.get("author").and_then(|v| v.as_array()) {
        for author in authors {
            if let Some(author_str) = author.as_str() {
                if author_str.to_lowercase().contains(&search_lower) {
                    return true;
                }
            }
        }
    }

    // Search in publication
    if let Some(pub_name) = doc.get("pub").and_then(|v| v.as_str()) {
        if pub_name.to_lowercase().contains(&search_lower) {
            return true;
        }
    }

    // Search in abstract
    if let Some(abstract_text) = doc.get("abstract").and_then(|v| v.as_str()) {
        if abstract_text.to_lowercase().contains(&search_lower) {
            return true;
        }
    }

    // Search in bibcode
    if let Some(bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
        if bibcode.to_lowercase().contains(&search_lower) {
            return true;
        }
    }

    false
}

fn highlight_text(text: &str, search_term: &str) -> String {
    if search_term.is_empty() {
        return text.to_string();
    }

    let search_lower = search_term.to_lowercase();
    let text_lower = text.to_lowercase();

    if let Some(start) = text_lower.find(&search_lower) {
        let end = start + search_term.len();
        let before = &text[..start];
        let matched = &text[start..end];
        let after = &text[end..];

        format!("{}{}{}",
            before,
            style(matched).bold().yellow(),
            highlight_text(after, search_term) // Recursively highlight remaining matches
        )
    } else {
        text.to_string()
    }
}

fn format_paper_short_with_highlight(doc: &serde_json::Value, search_term: &str) -> String {
    let title = doc.get("title")
        .and_then(|v| v.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let first_author = doc.get("first_author")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let year = doc.get("year")
        .and_then(|v| v.as_str())
        .unwrap_or("N/A");

    let citation_count = doc.get("citation_count")
        .and_then(|v| v.as_u64())
        .unwrap_or(0);

    // Truncate title if too long for better display in selection
    let truncated_title = if title.len() > 55 {
        format!("{}...", &title[..52])
    } else {
        title.to_string()
    };

    // Apply highlighting
    let highlighted_title = highlight_text(&truncated_title, search_term);
    let highlighted_author = highlight_text(first_author, search_term);

    // Color coding based on citation count
    let author_styled = if citation_count > 100 {
        style(highlighted_author).bold().yellow()
    } else if citation_count > 50 {
        style(highlighted_author).bold().cyan()
    } else {
        style(highlighted_author).white()
    };

    let year_styled = style(year).dim();
    let citations_styled = if citation_count > 0 {
        style(format!("({}🔗)", citation_count)).dim().green()
    } else {
        style(String::new()).dim()
    };

    format!("{} {} - {} {}",
        author_styled,
        year_styled,
        highlighted_title,
        citations_styled
    )
}

async fn search_cached_papers(page_cache: &HashMap<u32, (Vec<serde_json::Value>, u32)>) -> Result<PageAction> {
    let term = Term::stdout();
    let mut search_query = String::new();
    let mut selected_index = 0usize;
    let mut search_mode = true; // true = typing search, false = selecting papers

    loop {
        // Clear screen and show search interface
        term.clear_screen()?;

        println!("{}{} {}",
            style(format!("{}", MAGNIFY)).blue(),
            style("Search Cached Papers").bold().blue(),
            if search_mode {
                style("(Type to filter, Tab to select, Esc to exit)").dim()
            } else {
                style("(↑↓ select, Enter to view, Tab to search, Esc to exit)").dim()
            }
        );

        println!("\n{}Search: {}{}",
            style("🔍 ").blue(),
            style(&search_query).bold().yellow(),
            if search_mode { style("_").blink().to_string() } else { "".to_string() }
        );

        // Collect all cached papers
        let mut all_papers = Vec::new();
        for (page_num, (docs, _)) in page_cache.iter() {
            for (doc_index, doc) in docs.iter().enumerate() {
                all_papers.push(((*page_num, doc_index), doc));
            }
        }

        // Filter papers based on search query
        let filtered_papers: Vec<_> = all_papers.iter()
            .filter(|(_, doc)| paper_matches_search(doc, &search_query))
            .collect();

        println!("\n{}Found {} matching papers in cache:",
            style("📊 ").green(),
            style(filtered_papers.len().to_string()).bold()
        );

        if filtered_papers.is_empty() {
            println!("\n{}No papers match your search term",
                style("📭").yellow());
            selected_index = 0;
        } else {
            // Ensure selected_index is within bounds
            if selected_index >= filtered_papers.len() {
                selected_index = 0;
            }

            println!();
            let display_count = std::cmp::min(filtered_papers.len(), 10);
            for (i, ((page, _), doc)) in filtered_papers.iter().enumerate().take(display_count) {
                let formatted = format_paper_short_with_highlight(doc, &search_query);

                if !search_mode && i == selected_index {
                    // Highlighted/selected item
                    println!("{}▶ {} {}",
                        style(format!("{:2}", i + 1)).bold().yellow(),
                        style(formatted).bold().white(),
                        style(format!("(page {})", page + 1)).bold().cyan()
                    );
                } else {
                    // Regular item
                    println!("{}  {} {}",
                        style(format!("{:2}", i + 1)).dim(),
                        formatted,
                        style(format!("(page {})", page + 1)).dim()
                    );
                }
            }

            if filtered_papers.len() > 10 {
                println!("{}... and {} more",
                    style("").dim(),
                    style((filtered_papers.len() - 10).to_string()).dim()
                );
            }
        }

        let instructions = if search_mode {
            "Type to search, Tab to select papers, Enter/Esc to exit"
        } else {
            "↑↓ select paper, Enter to view, Tab to search, Esc to exit"
        };

        println!("\n{}{}",
            style("⌨️  ").blue(),
            style(instructions).dim()
        );

        // Handle keyboard input
        match term.read_key()? {
            Key::Char(c) if search_mode && (c.is_alphanumeric() || c.is_ascii_punctuation() || c == ' ') => {
                search_query.push(c);
                selected_index = 0; // Reset selection when search changes
            }
            Key::Backspace if search_mode => {
                search_query.pop();
                selected_index = 0; // Reset selection when search changes
            }
            Key::Tab => {
                // Toggle between search mode and selection mode
                search_mode = !search_mode;
                if !search_mode && filtered_papers.is_empty() {
                    search_mode = true; // Stay in search mode if no results
                }
            }
            Key::ArrowUp if !search_mode && !filtered_papers.is_empty() => {
                if selected_index > 0 {
                    selected_index -= 1;
                }
            }
            Key::ArrowDown if !search_mode && !filtered_papers.is_empty() => {
                let display_count = std::cmp::min(filtered_papers.len(), 10);
                if selected_index < display_count - 1 {
                    selected_index += 1;
                }
            }
            Key::Enter => {
                if !search_mode && !filtered_papers.is_empty() && selected_index < filtered_papers.len() {
                    // User selected a paper - we need to return which paper they selected
                    // For now, let's display the paper details and then return to search
                    let ((_page, _doc_index), doc) = filtered_papers[selected_index];
                    display_paper_details(doc);

                    // Handle paper actions
                    loop {
                        match handle_paper_actions(doc).await? {
                            PaperAction::BackToList => break, // Return to search
                            PaperAction::Quit => return Ok(PageAction::Quit),
                            PaperAction::ShowReferences => {
                                if let Some(selected_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("References", selected_bibcode, 10)).await?;
                                }
                            }
                            PaperAction::ShowCitations => {
                                if let Some(selected_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("Citations", selected_bibcode, 10)).await?;
                                }
                            }
                            PaperAction::ShowSimilar => {
                                if let Some(selected_bibcode) = doc.get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("Similar Papers", selected_bibcode, 10)).await?;
                                }
                            }
                            PaperAction::CopyBibtex | PaperAction::OpenInBrowser => {
                                continue; // Stay in the action menu after these actions
                            }
                        }
                    }
                } else {
                    return Ok(PageAction::Quit); // Exit search mode
                }
            }
            Key::Escape => {
                return Ok(PageAction::Quit);
            }
            _ => {
                // Ignore other keys
            }
        }
    }
}

async fn start_research_search(search_type: &str, bibcode: &str, rows: u32) -> Result<()> {
    println!("\n{}{} Research: {} {}",
        style("🔬").blue(),
        style(search_type).bold().blue(),
        style("Starting new search for").dim(),
        style(bibcode).yellow()
    );

    let response = match search_type {
        "References" => get_paper_references(bibcode, rows * 2).await?,
        "Citations" => get_paper_citations(bibcode, rows * 2).await?,
        "Similar Papers" => get_similar_papers(bibcode, rows * 2).await?,
        _ => return Err(anyhow::anyhow!("Unknown search type: {}", search_type)),
    };

    if response.response.docs.is_empty() {
        println!("\n{}No {} found for this paper.",
            style("📭").yellow(),
            search_type.to_lowercase()
        );
        println!("Press Enter to continue...");
        let mut input = String::new();
        std::io::stdin().read_line(&mut input).ok();
        return Ok(());
    }

    println!("{}Found {} {}! Starting interactive browse...",
        style(format!("{}", SUCCESS)).green(),
        response.response.num_found,
        search_type.to_lowercase()
    );

    // Start a new interactive session with these results
    let mut current_page = 0u32;
    let mut page_cache: HashMap<u32, (Vec<serde_json::Value>, u32)> = HashMap::new();

    // Cache the first page (and potentially second page)
    let total_results = response.response.num_found;
    let all_docs = response.response.docs;

    let current_page_docs: Vec<_> = all_docs.iter()
        .take(rows as usize)
        .cloned()
        .collect();

    let next_page_docs: Vec<_> = all_docs.iter()
        .skip(rows as usize)
        .take(rows as usize)
        .cloned()
        .collect();

    page_cache.insert(0, (current_page_docs, total_results));
    if !next_page_docs.is_empty() {
        page_cache.insert(1, (next_page_docs, total_results));
    }

    // Start the interactive pagination loop for this research search
    loop {
        let (docs, total_results) = if page_cache.contains_key(&current_page) {
            let (cached_docs, cached_total) = page_cache.get(&current_page).unwrap();
            let result = (cached_docs.clone(), *cached_total);

            // Pre-cache next page if needed
            let next_page = current_page + 1;
            let max_page = (cached_total + rows - 1) / rows;

            if next_page < max_page && !page_cache.contains_key(&next_page) {
                let _start = next_page * rows;
                let _search_fields = "bibcode,title,first_author,year,author,pub,citation_count,abstract";

                // Use the appropriate search function
                if let Ok(response) = match search_type {
                    "References" => get_paper_references(bibcode, rows).await,
                    "Citations" => get_paper_citations(bibcode, rows).await,
                    "Similar Papers" => get_similar_papers(bibcode, rows).await,
                    _ => continue,
                } {
                    if !response.response.docs.is_empty() {
                        page_cache.insert(next_page, (response.response.docs, response.response.num_found));
                    }
                }
            }

            result
        } else {
            // This shouldn't happen with our pre-caching, but handle it
            break;
        };

        match show_paginated_papers(&docs, current_page, total_results, rows)? {
            PageAction::SelectPaper(index) => {
                display_paper_details(&docs[index]);

                loop {
                    match handle_paper_actions(&docs[index]).await? {
                        PaperAction::BackToList => break,
                        PaperAction::Quit => return Ok(()),
                        PaperAction::ShowReferences => {
                            if let Some(selected_bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                Box::pin(start_research_search("References", selected_bibcode, rows)).await?;
                            }
                        }
                        PaperAction::ShowCitations => {
                            if let Some(selected_bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                Box::pin(start_research_search("Citations", selected_bibcode, rows)).await?;
                            }
                        }
                        PaperAction::ShowSimilar => {
                            if let Some(selected_bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                Box::pin(start_research_search("Similar Papers", selected_bibcode, rows)).await?;
                            }
                        }
                        PaperAction::CopyBibtex | PaperAction::OpenInBrowser => {
                            continue;
                        }
                    }
                }
            }
            PageAction::NextPage => {
                current_page += 1;
            }
            PageAction::PrevPage => {
                if current_page > 0 {
                    current_page -= 1;
                }
            }
            PageAction::SearchMode => {
                match search_cached_papers(&page_cache).await? {
                    PageAction::Quit => {
                        // Continue with normal pagination
                    }
                    _ => {}
                }
            }
            PageAction::Quit => break,
        }
    }

    Ok(())
}

fn setup_api_token() -> Result<String> {
    println!("{}{}",
        style(format!("{}", ROCKET)).blue(),
        style("Welcome to NASA ADS CLI!").bold().blue()
    );
    println!();

    println!("{}It looks like you haven't set up your ADS API token yet.",
        style("🔑").yellow()
    );
    println!("{}You'll need a free API token to search the NASA/ADS database.",
        style("").dim()
    );
    println!();

    println!("{}Opening your browser to get an API token...",
        style(format!("{}", BROWSER)).green()
    );

    let token_url = "https://ui.adsabs.harvard.edu/user/settings/token";
    if let Err(e) = webbrowser::open(token_url) {
        println!("{}Failed to open browser automatically: {}",
            style(format!("{}", ERROR)).red(), e
        );
        println!("{}Please manually visit: {}",
            style("🌐").blue(),
            style(token_url).underlined()
        );
    }

    println!();
    println!("{}Instructions:", style("📋").blue());
    println!("1. {}Log in to your ADS account (or create one if needed)", style("").dim());
    println!("2. {}Copy the API token from the settings page", style("").dim());
    println!("3. {}Paste it below", style("").dim());
    println!();

    // Get token from user
    let token_input = dialoguer::Input::<String>::new()
        .with_prompt(&format!("{}Please paste your ADS API token", style("🔑").yellow()))
        .validate_with(|input: &String| -> std::result::Result<(), &str> {
            if input.trim().is_empty() {
                Err("API token cannot be empty")
            } else if input.trim().len() < 10 {
                Err("API token seems too short")
            } else {
                Ok(())
            }
        })
        .interact()
        .context("Failed to read token input. Please ensure you're running in an interactive terminal.")?;

    let token = token_input.trim().to_string();

    // Save token to shell config
    if let Err(e) = save_token_to_shell_config(&token) {
        println!("{}Warning: Could not automatically save token to shell config: {}",
            style(format!("{}", ERROR)).yellow(), e
        );
        println!("{}Please manually add this line to your shell config file (~/.bashrc, ~/.zshrc, etc.):",
            style("💡").blue()
        );
        println!("{}export ADS_API_TOKEN=\"{}\"",
            style("").bold().green(),
            token
        );
        println!();
    } else {
        println!("{}{}",
            style(format!("{}", SUCCESS)).green(),
            style("API token saved! It will be available in new terminal sessions.").bold()
        );
        println!();
    }

    println!("{}{}",
        style(format!("{}", SUCCESS)).green(),
        style("Token is now active for this session - no need to restart your terminal!").bold()
    );
    println!("{}Setup complete! Continuing with your search...",
        style(format!("{}", SUCCESS)).green()
    );
    println!();

    Ok(token)
}

fn save_token_to_shell_config(token: &str) -> Result<()> {
    use std::fs::OpenOptions;
    use std::io::{Write, BufRead, BufReader};
    use std::path::PathBuf;

    let home_dir = env::var("HOME").context("Could not find HOME directory")?;
    let export_line = format!("export ADS_API_TOKEN=\"{}\"\n", token);

    // Try different shell config files
    let config_files = vec![
        PathBuf::from(&home_dir).join(".bashrc"),
        PathBuf::from(&home_dir).join(".zshrc"),
        PathBuf::from(&home_dir).join(".bash_profile"),
        PathBuf::from(&home_dir).join(".profile"),
    ];

    let mut saved_to = None;

    for config_file in config_files {
        if config_file.exists() {
            // Check if token already exists in file
            if let Ok(file) = std::fs::File::open(&config_file) {
                let reader = BufReader::new(file);
                let mut token_exists = false;

                for line in reader.lines() {
                    if let Ok(line) = line {
                        if line.contains("ADS_API_TOKEN") {
                            token_exists = true;
                            break;
                        }
                    }
                }

                if token_exists {
                    println!("{}ADS_API_TOKEN already exists in {}. Please update it manually if needed.",
                        style("ℹ️").blue(),
                        config_file.display()
                    );
                    continue;
                }
            }

            // Append token to file
            if let Ok(mut file) = OpenOptions::new()
                .create(true)
                .append(true)
                .open(&config_file) {

                writeln!(file, "\n# NASA ADS CLI API Token")?;
                write!(file, "{}", export_line)?;
                saved_to = Some(config_file);
                break;
            }
        }
    }

    if let Some(config_file) = saved_to {
        println!("{}Token saved to: {}",
            style("💾").green(),
            config_file.display()
        );
        Ok(())
    } else {
        Err(anyhow::anyhow!("Could not find or write to any shell config file"))
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    // Check if API token is available FIRST
    let api_token = match env::var("ADS_API_TOKEN") {
        Ok(token) if !token.trim().is_empty() => token,
        _ => {
            // Token not set or empty, run setup
            let token = setup_api_token()?;

            // After setup, check if user provided a query
            let query = cli.query_parts.join(" ");
            if query.is_empty() {
                println!("{}Great! You're all set up with your API token.",
                    style(format!("{}", SUCCESS)).green()
                );
                println!("{}Your token is active in this terminal session and saved for future sessions.",
                    style("🎯").blue()
                );
                println!("{}Now you can start searching! Try commands like:",
                    style("💡").blue()
                );
                println!("  {}ads author:Einstein", style("").bold().cyan());
                println!("  {}ads stochastic background", style("").bold().cyan());
                println!("  {}ads \"dark matter\" AND year:2023", style("").bold().cyan());
                return Ok(());
            }
            token
        }
    };

    // Set the token for this session
    env::set_var("ADS_API_TOKEN", &api_token);

    // Join all query parts into a single string
    let query = cli.query_parts.join(" ");

    if query.is_empty() {
        eprintln!("{}Error: Please provide a search query", style(format!("{}", ERROR)).red());
        eprintln!("Example: ads author:Einstein");
        eprintln!("Example: ads stochastic background");
        std::process::exit(1);
    }

    let rows = cli.rows;
    let fields = &cli.fields;
    let no_interactive = cli.no_interactive;

    println!("{}{} {}",
        style(format!("{}", TELESCOPE)).blue(),
        style("Searching ADS for:").bold().blue(),
        style(&query).bold().yellow()
    );
    println!("{}Requesting {} results per page with fields: {}",
        style(format!("{}", ROCKET)).dim(),
        style(rows.to_string()).cyan(),
        style(fields).dim()
    );
    println!();

    // For interactive mode, we want more fields to show detailed information
    let search_fields = if !no_interactive {
        format!("{},author,pub,citation_count,abstract", fields)
    } else {
        fields.clone()
    };

    if !no_interactive {
        // Interactive mode with pagination and caching
        let mut current_page = 0u32;
        let mut page_cache: HashMap<u32, (Vec<serde_json::Value>, u32)> = HashMap::new(); // page -> (docs, total_results)

        loop {
            // Check cache and pre-cache logic
            let (docs, total_results) = if page_cache.contains_key(&current_page) {
                // Get current page data first
                let (cached_docs, cached_total) = page_cache.get(&current_page).unwrap();
                let result = (cached_docs.clone(), *cached_total);

                // Now we can safely modify the cache for pre-caching
                let next_page = current_page + 1;
                let max_page = (cached_total + rows - 1) / rows;

                // If next page exists and isn't cached, fetch it now
                if next_page < max_page && !page_cache.contains_key(&next_page) {
                    let start = next_page * rows;

                    // Fetch next page quietly in foreground
                    if let Ok(response) = search_ads(&query, &search_fields, rows, start).await {
                        if !response.response.docs.is_empty() {
                            page_cache.insert(next_page, (response.response.docs, response.response.num_found));
                        }
                    }
                }

                result
            } else {
                let start = current_page * rows;

                // Show loading message only for API calls
                print!("{}Fetching pages {} and {} from ADS...",
                    style(format!("{}", LOADING)).blue(),
                    style((current_page + 1).to_string()).bold(),
                    style((current_page + 2).to_string()).bold()
                );
                Write::flush(&mut std::io::stdout()).unwrap();

                // Fetch double the results to pre-cache the next page
                let fetch_rows = rows * 2;
                let response = search_ads(&query, &search_fields, fetch_rows, start).await?;

                if response.response.docs.is_empty() && current_page == 0 {
                    println!("\n{}No papers found. Try adjusting your search query.",
                        style("📭").yellow());
                    return Ok(());
                }

                // Clear the loading message
                print!("\r{}", " ".repeat(60));
                print!("\r");
                Write::flush(&mut std::io::stdout()).unwrap();

                let total = response.response.num_found;
                let all_docs = response.response.docs;

                // Split results between current page and next page
                let current_page_docs: Vec<_> = all_docs.iter()
                    .take(rows as usize)
                    .cloned()
                    .collect();

                let next_page_docs: Vec<_> = all_docs.iter()
                    .skip(rows as usize)
                    .take(rows as usize)
                    .cloned()
                    .collect();

                // Cache current page
                page_cache.insert(current_page, (current_page_docs.clone(), total));

                // Pre-cache next page if we have results for it
                if !next_page_docs.is_empty() {
                    page_cache.insert(current_page + 1, (next_page_docs, total));
                }

                (current_page_docs, total)
            };

            // Show pagination interface
            match show_paginated_papers(&docs, current_page, total_results, rows)? {
                PageAction::SelectPaper(index) => {
                    // Display paper details
                    display_paper_details(&docs[index]);

                    // Show action menu and handle the result
                    loop {
                        match handle_paper_actions(&docs[index]).await? {
                            PaperAction::BackToList => break, // Go back to paper list
                            PaperAction::Quit => return Ok(()), // Exit the program
                            PaperAction::ShowReferences => {
                                if let Some(bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("References", bibcode, rows)).await?;
                                }
                            }
                            PaperAction::ShowCitations => {
                                if let Some(bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("Citations", bibcode, rows)).await?;
                                }
                            }
                            PaperAction::ShowSimilar => {
                                if let Some(bibcode) = docs[index].get("bibcode").and_then(|v| v.as_str()) {
                                    Box::pin(start_research_search("Similar Papers", bibcode, rows)).await?;
                                }
                            }
                            PaperAction::CopyBibtex | PaperAction::OpenInBrowser => {
                                // Stay in the action menu after these actions
                                continue;
                            }
                        }
                    }
                }
                PageAction::NextPage => {
                    current_page += 1;
                }
                PageAction::PrevPage => {
                    if current_page > 0 {
                        current_page -= 1;
                    }
                }
                PageAction::SearchMode => {
                    // Enter search mode
                    match search_cached_papers(&page_cache).await? {
                        PageAction::Quit => {
                            // Continue with normal pagination
                        }
                        _ => {
                            // Handle other actions if needed
                        }
                    }
                }
                PageAction::Quit => break,
            }
        }
    } else {
        // Plain text mode - show first page only
        let response = search_ads(&query, &search_fields, rows, 0).await?;

        let results_text = format!("Found {} total results, showing first {}:",
            response.response.num_found, response.response.docs.len());
        println!("{}{}", style(format!("{}", SEARCH)).green(), style(results_text).bold());

        if response.response.docs.is_empty() {
            println!("\n{}No papers found. Try adjusting your search query.",
                style("📭").yellow());
            return Ok(());
        }

        println!();
        for (i, doc) in response.response.docs.iter().enumerate() {
            println!("{}. {}", i + 1, format_paper(doc));
        }
    }

    Ok(())
}