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

import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class AthenaUDFHandlerTest
{
    private AthenaUDFHandler athenaUDFHandler;

    @Before
    public void setup()
    {
        this.athenaUDFHandler = new AthenaUDFHandler();
    }

    @Test
    public void testCompareJsonPathDateToDate()
    {
        String json = "{\"event\":{\"createdAt\":\"2024-01-02T00:00:00Z\"}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.event.createdAt", ">", "2024-01-01T00:00:00Z"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.event.createdAt", "<", "2024-01-01T00:00:00Z"));
    }

    @Test
    public void testCompareJsonPathDateToIntReturnsFalse()
    {
        String json = "{\"event\":{\"createdAt\":\"2024-01-02T00:00:00Z\"}}";
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.event.createdAt", ">", "1000"));
    }

    @Test
    public void testCompareJsonPathNumberToNumber()
    {
        String json = "{\"metrics\":{\"latencyMs\":\"12.5\"}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.metrics.latencyMs", "<=", "13"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.metrics.latencyMs", ">", "13"));
    }

    @Test
    public void testCompareJsonPathStringRegex()
    {
        String json = "{\"user\":{\"email\":\"abc123@example.com\"}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.user.email", "regex", "^[a-z]{3}\\d{3}@example\\.com$"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.user.email", "regex", "^xyz.*$"));
    }

    @Test
    public void testCompareJsonPathInvalidRegexReturnsFalse()
    {
        String json = "{\"user\":{\"email\":\"abc123@example.com\"}}";
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.user.email", "regex", "*invalid("));
    }

    @Test
    public void testCompareJsonPathBooleanChecks()
    {
        String json = "{\"flags\":{\"enabled\":\"true\",\"archived\":\"false\"}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.flags.enabled", "=", "true"));
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.flags.archived", "!=", "true"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.flags.enabled", ">", "false"));
    }

    @Test
    public void testCompareJsonPathWildcardAnyMatch()
    {
        String json = "{\"a\":{\"b\":[{\"c\":{\"x\":\"1\"}},{\"c\":{\"x\":\"3\"}}]}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.a.b[*].c.x", "=", "3"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.a.b[*].c.x", "=", "2"));
    }

    @Test
    public void testCompareJsonPathNestedWildcardAnyMatch()
    {
        String json = "{\"a\":{\"b\":[{\"c\":[{\"x\":\"foo\"},{\"x\":\"bar\"}]},{\"c\":[{\"x\":\"baz\"}]}]}}";
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.a.b[*].c[*].x", "=", "bar"));
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.a.b[*].c[*].x", "=", "qux"));
    }

    @Test
    public void testCompareJsonPathIntentionallyPositionedMatch()
    {
        String json = "{\"a\":{\"b\":[{\"c\":[{\"x\":\"needle\"}]},{\"c\":[{\"x\":\"hay\"},{\"x\":\"stack\"}]}]}}";
        assertFalse(athenaUDFHandler.comparejsonpath(json, "$.a.b[1].c[*].x", "=", "needle"));
        assertTrue(athenaUDFHandler.comparejsonpath(json, "$.a.b[0].c[*].x", "=", "needle"));
    }
}
