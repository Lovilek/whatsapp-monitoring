export function toCanonicalPayload({
    messageId,
    chatId,
    chatName,
    senderId,
    senderName,
    senderNumber,
    body,
    timestampMs,
    isGroup,
    type,
}) {
    return {
        id: messageId,
        chat_id: chatId,
        chat: chatName,
        sender_id: senderId,
        sender: senderName,
        sender_number: senderNumber,
        message: body,
        type,
        is_group: isGroup,
        timestamp: new Date(timestampMs).toISOString(),
        ts_ms: timestampMs
    };
}


