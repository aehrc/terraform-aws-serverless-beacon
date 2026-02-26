/*-
 * #%L
 * athena-udfs
 * %%
 * Copyright (C) 2019 Amazon Web Services
 * %%
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * #L%
 */
package com.amazonaws.athena.connectors.udfs;

import com.amazonaws.athena.connector.lambda.handlers.UserDefinedFunctionHandler;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

public class AthenaUDFHandler
        extends UserDefinedFunctionHandler
{
    private static final String SOURCE_TYPE = "athena_common_udfs";
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final Pattern NUMBER_PATTERN = Pattern.compile("^-?\\d+(\\.\\d+)?$");
    private static final Pattern BOOLEAN_PATTERN = Pattern.compile("^(?i:true|false)$");
    private static final Pattern DATE_PATTERN = Pattern.compile("^\\d{4}-\\d{2}-\\d{2}([T\\s]\\d{2}:\\d{2}:\\d{2}(\\.\\d{1,9})?)?([zZ]|[+-]\\d{2}:?\\d{2})?$");
    private static final Pattern PATH_TOKEN_PATTERN = Pattern.compile("([^\\[\\]]+)|\\[(\\d+)\\]");

    public AthenaUDFHandler()
    {
        super(SOURCE_TYPE);
    }

    /**
     * Extracts a value from JSON using a simple path (for example: $.a.b[0].c) and compares it with the provided
     * input using one of the supported operators.
     *
     * Supported comparison modes:
     * 1) ISO date string vs ISO date string with operators: >, >=, =, <, <= (also gt, gte, eq, lt, lte)
     * 2) boolean vs boolean with operators: =, !=
     * 3) number vs number with operators above
     * 4) string vs regex using operators: regex, matches, ~
     *
     * @param jsonInput JSON document string.
     * @param jsonPath Simple path expression (dot notation + array indexes).
     * @param filter Comparison operator.
     * @param comparisonValue Right-hand value as string.
     * @return true when comparison succeeds; false for invalid path/type/operator combinations.
     */
    public Boolean comparejsonpath(String jsonInput, String jsonPath, String filter, String comparisonValue)
    {
        String leftValue = extractjsonpathvalue(jsonInput, jsonPath);
        if (leftValue == null || filter == null || comparisonValue == null) {
            return false;
        }

        String operator = normalizeoperator(filter);
        if (operator == null) {
            return false;
        }

        if ("regex".equals(operator)) {
            try {
                return Pattern.compile(comparisonValue).matcher(leftValue).find();
            }
            catch (PatternSyntaxException e) {
                return false;
            }
        }

        if (lookslikedate(leftValue) && lookslikedate(comparisonValue)) {
            return comparestringbyorder(leftValue, comparisonValue, operator);
        }

        if (lookslikeboolean(leftValue) && lookslikeboolean(comparisonValue)) {
            return compareboolean(leftValue, comparisonValue, operator);
        }

        if (lookslikenumber(leftValue) && lookslikenumber(comparisonValue)) {
            BigDecimal leftNumber = new BigDecimal(leftValue);
            BigDecimal rightNumber = new BigDecimal(comparisonValue);
            return comparebigdecimal(leftNumber, rightNumber, operator);
        }

        if ("=".equals(operator)) {
            return leftValue.equals(comparisonValue);
        }
        if ("!=".equals(operator)) {
            return !leftValue.equals(comparisonValue);
        }

        return false;
    }

    private String extractjsonpathvalue(String jsonInput, String jsonPath)
    {
        if (jsonInput == null || jsonPath == null) {
            return null;
        }

        JsonNode node;
        try {
            node = OBJECT_MAPPER.readTree(jsonInput);
        }
        catch (JsonProcessingException e) {
            return null;
        }

        String normalizedPath = jsonPath.trim();
        if (normalizedPath.startsWith("$")) {
            normalizedPath = normalizedPath.substring(1);
            if (normalizedPath.startsWith(".")) {
                normalizedPath = normalizedPath.substring(1);
            }
        }

        if (normalizedPath.isEmpty()) {
            return node.isValueNode() ? node.asText() : node.toString();
        }

        String[] pathParts = normalizedPath.split("\\.");
        for (String pathPart : pathParts) {
            if (pathPart.isEmpty()) {
                continue;
            }

            Matcher matcher = PATH_TOKEN_PATTERN.matcher(pathPart);
            boolean foundToken = false;
            while (matcher.find()) {
                foundToken = true;
                if (matcher.group(1) != null) {
                    node = node.path(matcher.group(1));
                }
                else {
                    if (!node.isArray()) {
                        return null;
                    }
                    int index = Integer.parseInt(matcher.group(2));
                    if (index < 0 || index >= node.size()) {
                        return null;
                    }
                    node = node.get(index);
                }

                if (node == null || node.isMissingNode() || node.isNull()) {
                    return null;
                }
            }

            if (!foundToken) {
                return null;
            }
        }

        return node.isValueNode() ? node.asText() : node.toString();
    }

    private boolean comparebigdecimal(BigDecimal left, BigDecimal right, String operator)
    {
        int compared = left.compareTo(right);
        return comparebyorder(compared, operator);
    }

    private boolean comparestringbyorder(String left, String right, String operator)
    {
        int compared = left.compareTo(right);
        return comparebyorder(compared, operator);
    }

    private boolean comparebyorder(int compared, String operator)
    {
        if (">".equals(operator)) {
            return compared > 0;
        }
        if (">=".equals(operator)) {
            return compared >= 0;
        }
        if ("=".equals(operator)) {
            return compared == 0;
        }
        if ("<".equals(operator)) {
            return compared < 0;
        }
        if ("<=".equals(operator)) {
            return compared <= 0;
        }
        if ("!=".equals(operator)) {
            return compared != 0;
        }
        return false;
    }

    private boolean compareboolean(String left, String right, String operator)
    {
        boolean leftBool = Boolean.parseBoolean(left.trim().toLowerCase(Locale.ROOT));
        boolean rightBool = Boolean.parseBoolean(right.trim().toLowerCase(Locale.ROOT));
        if ("=".equals(operator)) {
            return leftBool == rightBool;
        }
        if ("!=".equals(operator)) {
            return leftBool != rightBool;
        }
        return false;
    }

    private String normalizeoperator(String filter)
    {
        String normalized = filter.trim().toLowerCase(Locale.ROOT);
        if ("gt".equals(normalized) || ">".equals(normalized)) {
            return ">";
        }
        if ("gte".equals(normalized) || ">=".equals(normalized)) {
            return ">=";
        }
        if ("eq".equals(normalized) || "=".equals(normalized) || "==".equals(normalized)) {
            return "=";
        }
        if ("lt".equals(normalized) || "<".equals(normalized)) {
            return "<";
        }
        if ("lte".equals(normalized) || "<=".equals(normalized)) {
            return "<=";
        }
        if ("ne".equals(normalized) || "!=".equals(normalized)) {
            return "!=";
        }
        if ("regex".equals(normalized) || "matches".equals(normalized) || "~".equals(normalized)) {
            return "regex";
        }
        return null;
    }

    private boolean lookslikenumber(String value)
    {
        return NUMBER_PATTERN.matcher(value.trim()).matches();
    }

    private boolean lookslikedate(String value)
    {
        return DATE_PATTERN.matcher(value.trim()).matches();
    }

    private boolean lookslikeboolean(String value)
    {
        return BOOLEAN_PATTERN.matcher(value.trim()).matches();
    }
}
