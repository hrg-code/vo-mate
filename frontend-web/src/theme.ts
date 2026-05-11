import type { ThemeConfig } from "antd";

export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: "#2563eb",
    colorInfo: "#2563eb",
    colorSuccess: "#0f9f8f",
    colorWarning: "#b7791f",
    colorError: "#d64545",
    colorText: "#1f2328",
    colorTextSecondary: "#5b6472",
    colorBorder: "#dde2e8",
    colorBgLayout: "#f7f8fa",
    colorBgContainer: "#ffffff",
    borderRadius: 8,
    fontFamily:
      'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 36,
      fontWeight: 700
    },
    Card: {
      borderRadiusLG: 8
    },
    Drawer: {
      colorBgElevated: "#ffffff"
    },
    Input: {
      borderRadius: 8,
      controlHeight: 38
    },
    Select: {
      borderRadius: 8,
      controlHeight: 36
    },
    Table: {
      borderColor: "#dde2e8",
      headerBg: "#fbfcfd",
      headerColor: "#5b6472",
      rowHoverBg: "#f7f8fa"
    },
    Tag: {
      borderRadiusSM: 999
    }
  }
};
