import { Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { router } from "@/router";

export default function App() {
  return (
    <AppLayout>
      <Routes>{router}</Routes>
    </AppLayout>
  );
}
