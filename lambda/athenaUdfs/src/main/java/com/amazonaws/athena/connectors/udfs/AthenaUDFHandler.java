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
import com.jayway.jsonpath.Configuration;
import com.jayway.jsonpath.JsonPath;
import com.jayway.jsonpath.Option;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

public class AthenaUDFHandler
        extends UserDefinedFunctionHandler
{
    private static final String SOURCE_TYPE = "athena_common_udfs";
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private static final Configuration JSONPATH_CONFIGURATION = Configuration.defaultConfiguration()
            .addOptions(Option.ALWAYS_RETURN_LIST, Option.SUPPRESS_EXCEPTIONS);
    private static final Pattern NUMBER_PATTERN = Pattern.compile("^-?\\d+(\\.\\d+)?$");
    private static final Pattern BOOLEAN_PATTERN = Pattern.compile("^(?i:true|false)$");
    private static final Pattern DATE_PATTERN = Pattern.compile("^\\d{4}-\\d{2}-\\d{2}([T\\s]\\d{2}:\\d{2}:\\d{2}(\\.\\d{1,9})?)?([zZ]|[+-]\\d{2}:?\\d{2})?$");

    private enum PathTokenType
    {
        PROPERTY,
        ARRAY_INDEX,
        WILDCARD
    }

    private static class PathToken
    {
        private final PathTokenType type;
        private final String propertyName;
        private final Integer arrayIndex;

        private PathToken(PathTokenType type, String propertyName, Integer arrayIndex)
        {
            this.type = type;
            this.propertyName = propertyName;
            this.arrayIndex = arrayIndex;
        }

        private static PathToken property(String propertyName)
        {
            return new PathToken(PathTokenType.PROPERTY, propertyName, null);
        }

        private static PathToken arrayindex(int arrayIndex)
        {
            return new PathToken(PathTokenType.ARRAY_INDEX, null, arrayIndex);
        }

        private static PathToken wildcard()
        {
            return new PathToken(PathTokenType.WILDCARD, null, null);
        }
    }

    public AthenaUDFHandler()
    {
        super(SOURCE_TYPE);
    }

    /**
     * Extracts one or more values from JSON using JSONPath (for example: $.a.b[0].c, $.a.b[*].c[*].x) and compares
     * them with the provided
     * input using one of the supported operators.
     *
     * Supported comparison modes:
     * 1) ISO date string vs ISO date string with operators: >, >=, =, <, <= (also gt, gte, eq, lt, lte)
     * 2) boolean vs boolean with operators: =, !=
     * 3) number vs number with operators above
     * 4) string vs regex using operators: regex, matches, ~
     *
     * @param jsonInput JSON document string.
     * @param jsonPath JSONPath expression.
     * @param filter Comparison operator.
     * @param comparisonValue Right-hand value as string.
     * @return true when comparison succeeds; false for invalid path/type/operator combinations.
     */
    public Boolean comparejsonpath(String jsonInput, String jsonPath, String filter, String comparisonValue)
    {
        if (filter == null || comparisonValue == null) {
            return false;
        }

        String operator = normalizeoperator(filter);
        if (operator == null) {
            return false;
        }

        List<String> leftValues = extractjsonpathvalues(jsonInput, jsonPath);
        if (leftValues.isEmpty()) {
            return false;
        }

        for (String leftValue : leftValues) {
            if (comparevalue(leftValue, operator, comparisonValue)) {
                return true;
            }
        }

        return false;
    }

    private boolean comparevalue(String leftValue, String operator, String comparisonValue)
    {
        if (leftValue == null) {
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

    private List<String> extractjsonpathvalues(String jsonInput, String jsonPath)
    {
        if (jsonInput == null || jsonPath == null) {
            return Collections.emptyList();
        }

        String normalizedPath = normalizejsonpath(jsonPath);
        if (normalizedPath == null) {
            return Collections.emptyList();
        }

        List<String> values = extractjsonpathvaluesusingjsonpath(jsonInput, normalizedPath);
        if (!values.isEmpty()) {
            return values;
        }

        return extractjsonpathvaluescaseinsensitive(jsonInput, normalizedPath);
    }

    private List<String> extractjsonpathvaluesusingjsonpath(String jsonInput, String normalizedPath)
    {
        try {
            Object matchesObject = JsonPath.using(JSONPATH_CONFIGURATION)
                    .parse(jsonInput)
                    .read(normalizedPath);

            if (!(matchesObject instanceof List<?>)) {
                return Collections.emptyList();
            }

            return tomatchvalues((List<?>) matchesObject);
        }
        catch (RuntimeException e) {
            return Collections.emptyList();
        }
    }

    private List<String> extractjsonpathvaluescaseinsensitive(String jsonInput, String jsonPath)
    {
        List<PathToken> tokens = parsejsonpathtokens(jsonPath);
        if (tokens == null) {
            return Collections.emptyList();
        }

        try {
            JsonNode root = OBJECT_MAPPER.readTree(jsonInput);
            List<JsonNode> currentNodes = new ArrayList<>();
            currentNodes.add(root);

            for (PathToken token : tokens) {
                List<JsonNode> nextNodes = new ArrayList<>();
                for (JsonNode currentNode : currentNodes) {
                    applypathtoken(currentNode, token, nextNodes);
                }
                if (nextNodes.isEmpty()) {
                    return Collections.emptyList();
                }
                currentNodes = nextNodes;
            }

            return tomatchvalues(currentNodes);
        }
        catch (JsonProcessingException e) {
            return Collections.emptyList();
        }
    }

    private List<PathToken> parsejsonpathtokens(String jsonPath)
    {
        if (jsonPath == null || jsonPath.isEmpty() || jsonPath.charAt(0) != '$') {
            return null;
        }

        List<PathToken> tokens = new ArrayList<>();
        int index = 1;
        while (index < jsonPath.length()) {
            char current = jsonPath.charAt(index);
            if (current == '.') {
                index++;
                if (index >= jsonPath.length()) {
                    break;
                }
                if (jsonPath.charAt(index) == '*') {
                    tokens.add(PathToken.wildcard());
                    index++;
                    continue;
                }

                int start = index;
                while (index < jsonPath.length()) {
                    char pathChar = jsonPath.charAt(index);
                    if (pathChar == '.' || pathChar == '[') {
                        break;
                    }
                    index++;
                }
                if (start == index) {
                    return null;
                }
                tokens.add(PathToken.property(jsonPath.substring(start, index)));
                continue;
            }

            if (current == '[') {
                int closingIndex = jsonPath.indexOf(']', index + 1);
                if (closingIndex < 0) {
                    return null;
                }

                String bracketContent = jsonPath.substring(index + 1, closingIndex).trim();
                if (bracketContent.isEmpty()) {
                    return null;
                }
                if ("*".equals(bracketContent)) {
                    tokens.add(PathToken.wildcard());
                }
                else if (isquotedproperty(bracketContent)) {
                    tokens.add(PathToken.property(bracketContent.substring(1, bracketContent.length() - 1)));
                }
                else {
                    try {
                        int arrayIndex = Integer.parseInt(bracketContent);
                        if (arrayIndex < 0) {
                            return null;
                        }
                        tokens.add(PathToken.arrayindex(arrayIndex));
                    }
                    catch (NumberFormatException e) {
                        return null;
                    }
                }

                index = closingIndex + 1;
                continue;
            }

            return null;
        }

        return tokens;
    }

    private boolean isquotedproperty(String value)
    {
        return value.length() >= 2
                && ((value.charAt(0) == '\'' && value.charAt(value.length() - 1) == '\'')
                || (value.charAt(0) == '"' && value.charAt(value.length() - 1) == '"'));
    }

    private void applypathtoken(JsonNode currentNode, PathToken token, List<JsonNode> nextNodes)
    {
        if (token.type == PathTokenType.PROPERTY) {
            addpropertymatchescaseinsensitive(currentNode, token.propertyName, nextNodes);
            return;
        }

        if (token.type == PathTokenType.ARRAY_INDEX) {
            if (currentNode.isArray() && token.arrayIndex < currentNode.size()) {
                nextNodes.add(currentNode.get(token.arrayIndex));
            }
            return;
        }

        if (token.type == PathTokenType.WILDCARD) {
            if (currentNode.isObject()) {
                Iterator<JsonNode> values = currentNode.elements();
                while (values.hasNext()) {
                    nextNodes.add(values.next());
                }
            }
            else if (currentNode.isArray()) {
                for (JsonNode arrayElement : currentNode) {
                    nextNodes.add(arrayElement);
                }
            }
        }
    }

    private void addpropertymatchescaseinsensitive(JsonNode currentNode, String propertyName, List<JsonNode> nextNodes)
    {
        if (!currentNode.isObject() || propertyName == null) {
            return;
        }

        Iterator<String> fieldNames = currentNode.fieldNames();
        while (fieldNames.hasNext()) {
            String fieldName = fieldNames.next();
            if (fieldName.equalsIgnoreCase(propertyName)) {
                JsonNode matchedNode = currentNode.get(fieldName);
                if (matchedNode != null) {
                    nextNodes.add(matchedNode);
                }
            }
        }
    }

    private String normalizejsonpath(String jsonPath)
    {
        String normalizedPath = jsonPath.trim();
        if (normalizedPath.isEmpty()) {
            return "$";
        }

        if (normalizedPath.startsWith("$")) {
            return normalizedPath;
        }

        if (normalizedPath.startsWith(".")) {
            return "$" + normalizedPath;
        }

        if (normalizedPath.startsWith("[")) {
            return "$" + normalizedPath;
        }

        return "$." + normalizedPath;
    }

    private List<String> tomatchvalues(List<?> matches)
    {
        List<String> values = new ArrayList<>();
        for (Object match : matches) {
            String value = tomatchvalue(match);
            if (value != null) {
                values.add(value);
            }
        }
        return values;
    }

    private String tomatchvalue(Object value)
    {
        if (value == null) {
            return null;
        }
        if (value instanceof String) {
            return (String) value;
        }
        if (value instanceof Number || value instanceof Boolean) {
            return String.valueOf(value);
        }
        if (value instanceof JsonNode) {
            JsonNode node = (JsonNode) value;
            return node.isValueNode() ? node.asText() : node.toString();
        }

        try {
            return OBJECT_MAPPER.writeValueAsString(value);
        }
        catch (JsonProcessingException e) {
            return null;
        }
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
