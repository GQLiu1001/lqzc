package src.test.java.com.lqzc.mcp.tool;

import com.lqzc.mcp.adapter.LqzcBackendClient;
import com.lqzc.mcp.dto.InventoryLookupResponse;
import com.lqzc.mcp.dto.TopSalesItem;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class MallMcpToolsTest {

    @Test
    void shouldDelegateInventoryLookupToBackendClient() {
        LqzcBackendClient backendClient = mock(LqzcBackendClient.class);
        com.lqzc.mcp.tool.MallMcpTools tools = new com.lqzc.mcp.tool.MallMcpTools(backendClient);
        InventoryLookupResponse expected = new InventoryLookupResponse(
                1L,
                "TA800-01",
                "LQZC",
                "800x800",
                2,
                "地砖",
                1,
                "抛光",
                3,
                "仓库3",
                120,
                4,
                new BigDecimal("168.00"),
                "热销型号"
        );

        when(backendClient.getInventoryByModel("TA800-01")).thenReturn(expected);

        InventoryLookupResponse actual = tools.getInventoryByModel("TA800-01");

        assertThat(actual).isEqualTo(expected);
        verify(backendClient).getInventoryByModel("TA800-01");
    }

    @Test
    void shouldReturnTopSalesFromBackendClient() {
        LqzcBackendClient backendClient = mock(LqzcBackendClient.class);
        com.lqzc.mcp.tool.MallMcpTools tools = new com.lqzc.mcp.tool.MallMcpTools(backendClient);
        List<TopSalesItem> expected = List.of(
                new TopSalesItem("TA800-01", 88),
                new TopSalesItem("TB600-09", 66)
        );

        when(backendClient.getTopSales()).thenReturn(expected);

        List<TopSalesItem> actual = tools.getTopSales();

        assertThat(actual).containsExactlyElementsOf(expected);
        verify(backendClient).getTopSales();
    }
}
