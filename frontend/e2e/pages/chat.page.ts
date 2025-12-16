/**
 * Chat Page Object
 * Story 5-0: Chat interface interactions
 *
 * Encapsulates chat page elements and actions for Story 5-0 automation testing
 * Knowledge Base References:
 * - test-quality.md: Page Object Model pattern
 * - network-first.md: Wait for network responses before assertions
 */

import { Page, expect, Locator } from '@playwright/test';
import { BasePage } from './base.page';

export class ChatPage extends BasePage {
  // Locators
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly messageList: Locator;
  readonly kbSelector: Locator;
  readonly clearChatButton: Locator;
  readonly undoButton: Locator;
  readonly newConversationButton: Locator;
  readonly conversationList: Locator;

  constructor(page: Page) {
    super(page);

    // Chat interface elements (based on Story 5-0 implementation)
    this.chatInput = this.page.getByTestId('chat-input');
    this.sendButton = this.page.getByTestId('send-message-button');
    this.messageList = this.page.getByTestId('message-list');
    this.kbSelector = this.page.getByTestId('kb-selector');
    this.clearChatButton = this.page.getByTestId('clear-chat-button');
    this.undoButton = this.page.getByTestId('undo-button');
    this.newConversationButton = this.page.getByTestId('new-conversation-button');
    this.conversationList = this.page.getByTestId('conversation-list');
  }

  async goto() {
    await super.goto('/chat');
  }

  /**
   * Send a chat message (network-first pattern)
   * @param message - Message text to send
   * @param waitForResponse - Wait for streaming response to complete (default: true)
   */
  async sendMessage(message: string, waitForResponse = true) {
    // Network-first: Set up response promise BEFORE triggering action
    const responsePromise = waitForResponse
      ? this.page.waitForResponse(
          (resp) => resp.url().includes('/api/v1/chat/stream') && resp.status() === 200,
          { timeout: 10000 }
        )
      : null;

    await this.chatInput.fill(message);
    await this.sendButton.click();

    if (responsePromise) {
      await responsePromise;
      // Wait for streaming to complete (look for send button to be re-enabled)
      await expect(this.sendButton).toBeEnabled({ timeout: 30000 });
    }
  }

  /**
   * Get all messages in the conversation
   * @returns Array of message objects with role and content
   */
  async getMessages(): Promise<Array<{ role: string; content: string }>> {
    const messages = await this.messageList.locator('[data-testid^="message-"]').all();
    const result: Array<{ role: string; content: string }> = [];

    for (const message of messages) {
      const role = await message.getAttribute('data-role');
      const content = await message.textContent();
      if (role && content) {
        result.push({ role, content: content.trim() });
      }
    }

    return result;
  }

  /**
   * Select a knowledge base from dropdown
   * @param kbName - Name of KB to select
   */
  async selectKnowledgeBase(kbName: string) {
    await this.kbSelector.click();
    await this.page.getByRole('option', { name: kbName }).click();
  }

  /**
   * Clear current conversation
   */
  async clearConversation() {
    await this.clearChatButton.click();
    // Confirm dialog if present
    const confirmButton = this.page.getByRole('button', { name: /confirm|yes/i });
    if (await confirmButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await confirmButton.click();
    }
  }

  /**
   * Undo last message
   */
  async undoLastMessage() {
    await this.undoButton.click();
  }

  /**
   * Start a new conversation
   */
  async startNewConversation() {
    await this.newConversationButton.click();
  }

  /**
   * Select a conversation from history
   * @param conversationTitle - Title or partial text of conversation
   */
  async selectConversation(conversationTitle: string) {
    const conversation = this.conversationList.locator('[data-testid^="conversation-"]').filter({
      hasText: conversationTitle,
    });
    await conversation.click();
  }

  /**
   * Wait for assistant message to appear and finish streaming
   * @param timeout - Maximum wait time in ms (default: 30000)
   */
  async waitForAssistantResponse(timeout = 30000) {
    // Wait for assistant message to appear
    const assistantMessage = this.messageList.locator('[data-testid="message-assistant"]').last();
    await expect(assistantMessage).toBeVisible({ timeout });

    // Wait for send button to be re-enabled (streaming complete)
    await expect(this.sendButton).toBeEnabled({ timeout });
  }

  /**
   * Verify empty state message is displayed
   */
  async expectEmptyState() {
    const emptyState = this.page.getByTestId('chat-empty-state');
    await expect(emptyState).toBeVisible();
  }

  /**
   * Verify no KB selected message is displayed
   */
  async expectNoKbSelectedMessage() {
    const noKbMessage = this.page.getByText(/select a knowledge base/i);
    await expect(noKbMessage).toBeVisible();
  }

  /**
   * Verify error message is displayed
   * @param errorText - Expected error text (partial match)
   */
  async expectErrorMessage(errorText: string | RegExp) {
    const errorMessage = this.page.getByTestId('chat-error-message');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText(errorText);
  }

  /**
   * Get citation links from last assistant message
   * @returns Array of citation numbers (e.g., [1, 2, 3])
   */
  async getCitationsFromLastMessage(): Promise<number[]> {
    const lastAssistantMessage = this.messageList.locator('[data-testid="message-assistant"]').last();
    const citations = await lastAssistantMessage.locator('[data-testid^="citation-"]').all();

    const citationNumbers: number[] = [];
    for (const citation of citations) {
      const citationText = await citation.textContent();
      const match = citationText?.match(/\[(\d+)\]/);
      if (match) {
        citationNumbers.push(parseInt(match[1], 10));
      }
    }

    return citationNumbers;
  }

  /**
   * Click a citation in the last assistant message
   * @param citationNumber - Citation number to click (e.g., 1 for [1])
   */
  async clickCitation(citationNumber: number) {
    const lastAssistantMessage = this.messageList.locator('[data-testid="message-assistant"]').last();
    const citation = lastAssistantMessage.locator(`[data-testid="citation-${citationNumber}"]`);
    await citation.click();
  }
}
