const STREAM_ENDPOINT =
  "/api/v1/research/report/stream";


async function parseHttpError(
  response,
) {
  try {
    const data =
      await response.json();

    if (
      typeof data?.detail ===
      "string"
    ) {
      return data.detail;
    }

    return JSON.stringify(
      data,
      null,
      2,
    );
  } catch {
    return (
      "Request failed with HTTP "
      + response.status
    );
  }
}


function parseEventBlock(
  block,
) {
  const lines =
    block.split("\n");

  let eventName =
    "message";

  const dataLines = [];

  for (const line of lines) {
    if (
      line.startsWith(
        "event:",
      )
    ) {
      eventName =
        line
          .slice(6)
          .trim();

      continue;
    }

    if (
      line.startsWith(
        "data:",
      )
    ) {
      dataLines.push(
        line
          .slice(5)
          .trimStart(),
      );
    }
  }

  if (!dataLines.length) {
    return null;
  }

  return {
    event: eventName,

    data: JSON.parse(
      dataLines.join(
        "\n",
      ),
    ),
  };
}


export async function runResearchStream(
  query,
  {
    signal,
    onProgress,
  } = {},
) {
  const response =
    await fetch(
      STREAM_ENDPOINT,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          Accept:
            "text/event-stream",
        },

        body: JSON.stringify({
          query,
        }),

        signal,
      },
    );

  if (!response.ok) {
    throw new Error(
      await parseHttpError(
        response,
      ),
    );
  }

  if (!response.body) {
    throw new Error(
      "Streaming response body "
      + "is unavailable.",
    );
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let buffer = "";
  let finalResult = null;

  while (true) {
    const {
      value,
      done,
    } = await reader.read();

    if (value) {
      buffer +=
        decoder.decode(
          value,
          {
            stream: !done,
          },
        );
    }

    buffer =
      buffer.replace(
        /\r\n/g,
        "\n",
      );

    const blocks =
      buffer.split(
        "\n\n",
      );

    buffer =
      blocks.pop() ?? "";

    for (
      const block
      of blocks
    ) {
      if (!block.trim()) {
        continue;
      }

      const parsed =
        parseEventBlock(
          block,
        );

      if (!parsed) {
        continue;
      }

      if (
        parsed.event ===
        "progress"
      ) {
        onProgress?.(
          parsed.data,
        );

        continue;
      }

      if (
        parsed.event ===
        "error"
      ) {
        throw new Error(
          parsed.data
            ?.detail ||
            "Research failed",
        );
      }

      if (
        parsed.event ===
        "result"
      ) {
        finalResult =
          parsed.data;
      }
    }

    if (done) {
      break;
    }
  }

  if (!finalResult) {
    throw new Error(
      "Research stream ended "
      + "without a final result.",
    );
  }

  return finalResult;
}
